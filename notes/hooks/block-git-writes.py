#!/usr/bin/env python3
"""Не даёт Клоду менять историю, индекс и ветки git своей командой.

Коммиты, push, pull и прочее делает пользователь. Запреты в
.claude/settings.json (`Bash(git commit *)` и т. п.) сравнивают начало
команды, поэтому `git -C notes commit` и `cd notes && git commit` мимо
них проходят. Этот хук смотрит на само действие git.

Как разбирает команду:
  1. shlex делит её на слова с учётом кавычек. `grep "git commit" f` —
     это grep с одним аргументом, а не git.
  2. Слова делятся на отдельные команды по `;`, `&&`, `||`, `|`, `(`, `)`
     и переводу строки.
  3. В каждой команде пропускаются `VAR=…` и обёртки (`sudo`, `env`,
     `timeout 10` …). Если дальше `git`, пропускаются его опции (`-C dir`,
     `-c k=v`, `--git-dir=…`), и следующее слово — действие.
  4. `bash -c "…"`, `sh -c "…"` и `eval …` разбираются так же, изнутри.
  5. Текст после `<<EOF` до строки `EOF` (heredoc) — данные для программы,
     а не команды, и не проверяется. Исключение — если его читает
     `bash`, `sh`, `zsh` или `dash`: тогда он проверяется как команды.

Не ловит: псевдонимы git (`git ci`), скрипты в файлах, команды внутри
строки в двойных кавычках (`echo "$(git commit)"`). Основная защита —
правило, что я эти команды не запускаю; хук — страховка от ошибки.
"""
import json
import os
import re
import shlex
import sys

# Действия git, которые меняют индекс, рабочие файлы, историю или ветку
# на GitHub. `clean` здесь нет: его отдельно сторожит protect-notes.sh.
BLOCKED = {
    "add", "rm", "mv", "commit", "push", "pull", "reset", "restore",
    "checkout", "switch", "merge", "rebase", "cherry-pick", "revert",
    "am", "apply", "stash",
}

# Опции самого git (до действия), после которых идёт отдельное значение.
GIT_OPTS_WITH_VALUE = {
    "-C", "-c", "--git-dir", "--work-tree", "--namespace",
    "--super-prefix", "--config-env", "--exec-path", "--list-cmds",
}

# Обёртки, которые запускают следующее слово как команду.
WRAPPERS = {"sudo", "env", "nice", "nohup", "time", "command", "exec", "xargs"}

SEPARATOR_CHARS = set(";&|()\n")
SHELLS = {"bash", "sh", "zsh", "dash"}

# `<<EOF`, `<<-EOF`, `<<'EOF'`, `<<"EOF"`; `<<<` (here-string) — не то.
HEREDOC = re.compile(r"(?<!<)<<(?!<)(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
SHELL_BEFORE = re.compile(r"(^|[\s;&|(])(bash|sh|zsh|dash)(\s|$)")


def split_heredocs(cmd):
    """Убрать тексты heredoc из команды.

    Вернуть команду без них и список текстов, которые читает shell:
    их надо проверить как команды."""
    lines = cmd.split("\n")
    kept, shell_bodies = [], []
    i = 0
    while i < len(lines):
        line = lines[i]
        kept.append(line)
        i += 1
        for m in HEREDOC.finditer(line):
            strip_tabs, delimiter = m.group(1) == "-", m.group(3)
            body = []
            while i < len(lines):
                end = lines[i].lstrip("\t") if strip_tabs else lines[i]
                i += 1
                if end == delimiter:
                    break
                body.append(lines[i - 1])
            if SHELL_BEFORE.search(line[: m.start()]):
                shell_bodies.append("\n".join(body))
    return "\n".join(kept), shell_bodies


def split_commands(cmd):
    lexer = shlex.shlex(cmd, posix=True, punctuation_chars=";&|()<>\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    commands, current = [], []
    for token in lexer:
        if token and set(token) <= SEPARATOR_CHARS:
            if current:
                commands.append(current)
            current = []
        else:
            current.append(token)
    if current:
        commands.append(current)
    return commands


def skip_prefix(words):
    """Пропустить `VAR=…` и обёртки, вернуть слова с настоящей команды."""
    i = 0
    while i < len(words):
        w = words[i]
        if "=" in w and not w.startswith("-") and w.split("=", 1)[0].isidentifier():
            i += 1
        elif os.path.basename(w) in WRAPPERS:
            i += 1
            # опции обёртки: `sudo -u x`, `env -i`, `nice -n 5`
            while i < len(words) and words[i].startswith("-"):
                i += 2 if words[i] in {"-u", "-n", "-g"} else 1
        elif w == "timeout":
            i += 1
            while i < len(words) and words[i].startswith("-"):
                i += 1
            i += 1  # длительность: `timeout 10`
        else:
            break
    return words[i:]


def git_action(words):
    """Для `git … действие …` вернуть действие, иначе None."""
    i = 1
    while i < len(words):
        w = words[i]
        if w in GIT_OPTS_WITH_VALUE:
            i += 2
        elif w.startswith("-"):
            i += 1
        else:
            return w
    return None


def find_blocked(cmd, depth=0):
    if depth > 5:
        return None
    cmd, shell_bodies = split_heredocs(cmd)
    for body in shell_bodies:
        found = find_blocked(body, depth + 1)
        if found:
            return found
    try:
        commands = split_commands(cmd)
    except ValueError:
        # Незакрытая кавычка: bash такую команду тоже не выполнит.
        return None
    for words in commands:
        words = skip_prefix(words)
        if not words:
            continue
        name = os.path.basename(words[0])
        if name == "git":
            action = git_action(words)
            if action in BLOCKED:
                return action
        elif name in SHELLS and "-c" in words[1:]:
            k = words.index("-c", 1)
            if k + 1 < len(words):
                found = find_blocked(words[k + 1], depth + 1)
                if found:
                    return found
        elif name == "eval":
            found = find_blocked(" ".join(words[1:]), depth + 1)
            if found:
                return found
    return None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command") or ""
    action = find_blocked(cmd)
    if action:
        print(
            f"ЗАБЛОКИРОВАНО хуком block-git-writes.py: git {action}.\n"
            f"Команда: {cmd}\n"
            "Коммиты, push, pull и другие изменения git делает пользователь.\n"
            "Назови изменённые файлы и предложи текст коммита.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
