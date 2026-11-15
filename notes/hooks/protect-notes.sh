#!/usr/bin/env bash
# Не даёт Claude удалить заметки своей же командой.
# Смотрит только на Bash: другими инструментами файл не удалить.
#
# Блокирует два случая:
#   1. git clean без -n и --dry-run. Он сносит игнорируемое, а notes/
#      и указатели на неё в проекте как раз лежат в .gitignore.
#   2. команду удаления, в которой упомянут защищённый путь.
#
# Перенос (mv) не блокируется намеренно: содержимое он не уничтожает,
# а при раскладке заметок по папкам переносить приходится постоянно.
set -u

input=$(cat)
[ "$(jq -r '.tool_name // empty' <<< "$input")" = "Bash" ] || exit 0
cmd=$(jq -r '.tool_input.command // empty' <<< "$input")
[ -n "$cmd" ] || exit 0

# Что защищает хук: notes/ и указатели на неё в проекте.
TARGETS='notes|settings\.local\.json|CLAUDE\.local\.md|answer-reviewer|skills/explain|skills/setup-project|rules/code-rules|rules/stack-rules'

deny() {
    {
        echo "ЗАБЛОКИРОВАНО хуком protect-notes.sh: $1"
        echo "Команда: $cmd"
        echo "Claude не удаляет заметки: notes/ и указатели на неё в проекте."
        echo "Если удалить нужно осознанно, попроси пользователя сделать это самому."
    } >&2
    exit 2
}

# Команда бывает составной. Хук делит её на части и смотрит на первое
# слово каждой: иначе `git rm --cached` не отличить от `rm`.
parts=$(sed 's/&&/\n/g; s/||/\n/g; s/[;|]/\n/g' <<< "$cmd")

while IFS= read -r part; do
    [ -n "$part" ] || continue

    # снять пробелы слева и обёртки, которые запускают следующее слово
    part=$(sed -E 's/^[[:space:]]+//; s/^(sudo|nohup|nice|time|timeout [0-9smh]+)[[:space:]]+//' <<< "$part")
    first=${part%% *}

    if [ "$first" = git ] && grep -qE '(^|[[:space:]])clean([[:space:]]|$)' <<< "$part"; then
        grep -qE -- '(^|[[:space:]])(-n|--dry-run)([[:space:]]|$)' <<< "$part" ||
            deny "git clean сносит игнорируемые файлы, а notes/ игнорируется."
    fi

    kills=0
    case "$first" in
        rm | rmdir | unlink | shred) kills=1 ;;
        find) grep -qE -- '-delete|-exec[[:space:]]+rm' <<< "$part" && kills=1 ;;
        rsync) grep -q -- '--delete' <<< "$part" && kills=1 ;;
    esac

    if [ "$kills" = 1 ] && grep -qE -- "$TARGETS" <<< "$part"; then
        deny "команда удаляет защищённый путь."
    fi
done <<< "$parts"

exit 0
