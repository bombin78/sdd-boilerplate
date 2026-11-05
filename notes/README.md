# Заметки к проекту <имя проекта>

<!--
  БОЛВАНКА. Замените <имя проекта> и адреса репозиториев в угловых
  скобках, затем удалите этот комментарий.
-->

Этот репозиторий — личные заметки к проекту <имя проекта>
(`<адрес репозитория проекта>`). Он лежит внутри папки проекта, в подпапке
`notes/`.
В проекте эта папка стоит в `.gitignore`, поэтому в историю проекта из неё
не попадает ничего. Коммиты в заметки делаются отсюда, из `notes/`, и делает
их пользователь, а не Claude.

Удалённый репозиторий заметок (закрытый):
`<адрес репозитория заметок>`.

## Что здесь лежит

```
├── README.md                          ← этот файл
├── CLAUDE.md                          ← правила работы с папкой notes
├── claude/
│   ├── answer-rules.md                ← правила ответов Claude
│   ├── common-rules.md                ← общие правила: git, долгие проверки, поиск
│   ├── code-rules.md                  ← правила кода: общие, без привязки к стеку
│   ├── stack-rules.md                 ← правила стека: технологии, документация, проверка
│   ├── agents/answer-reviewer.md      ← агент: проверяет черновик ответа
│   └── skills/
│       ├── explain/SKILL.md           ← скилл /explain
│       └── setup-project/SKILL.md     ← скилл /setup-project: стек и читатель
├── hooks/
│   ├── protect-notes.sh               ← хук: запрещает Claude удалять заметки
│   └── block-git-writes.py            ← хук: запрещает Claude коммиты, push, pull
├── docs/
│   ├── answers/                       ← сохранённые ответы
│   └── *.md                           ← разборы тем
├── ideas/                             ← идеи
├── tasks/                             ← задачи: что сделать, как проверить, что сделано
│   ├── README.md                      ← уровни, имена, порядок приёмки
│   ├── registry/                      ← списки задач: app.md, infra.md
│   ├── app/                           ← задачи приложения
│   └── infra/                         ← задачи инфраструктуры
└── *.md                               ← справочники: сервер, Docker, рекомендации
```

В `claude/` — личная настройка Claude Code: правила, скилл, агент. Папка
называется `claude`, а не `.claude`: Claude Code сам загружает скиллы
из `.claude/skills/` в подпапках проекта, и папка `notes/.claude/` дала бы
вторую копию скилла.

Правила загружаются по-разному:

| Файл | Когда Claude Code его загружает |
|---|---|
| `claude/answer-rules.md`, `claude/common-rules.md` | при старте сессии, через `CLAUDE.local.md` |
| `claude/code-rules.md`, `claude/stack-rules.md` | когда Claude читает или правит файл, подходящий под шаблоны `paths` в начале файла, через ссылки `.claude/rules/code-rules.md` и `.claude/rules/stack-rules.md` |
| `CLAUDE.md` | когда Claude читает или правит любой файл в `notes/`: `CLAUDE.md` в подпапке Claude Code загружает сам, указатель не нужен |

Файлы, которые загружаются не при старте, не видны в `/context` в списке
**Memory files**. Когда такой файл загружается, в терминале появляется
строка `Loaded` с его путём.

## Что нужно в проекте

Claude Code ищет правила, скиллы, агентов и настройки только на определённых
местах в проекте. Поэтому в корне проекта лежат семь указателей на файлы
этого репозитория. Все они стоят в `.gitignore` проекта, и в историю проекта
не попадают. Пути в таблице — от корня проекта:

| Указатель в проекте | На что указывает |
|---|---|
| `CLAUDE.local.md` | импорт `notes/claude/answer-rules.md` и `notes/claude/common-rules.md` |
| `.claude/rules/code-rules.md` | символическая ссылка на `notes/claude/code-rules.md` |
| `.claude/rules/stack-rules.md` | символическая ссылка на `notes/claude/stack-rules.md` |
| `.claude/skills/explain` | символическая ссылка на `notes/claude/skills/explain` |
| `.claude/skills/setup-project` | символическая ссылка на `notes/claude/skills/setup-project` |
| `.claude/agents/answer-reviewer.md` | символическая ссылка на `notes/claude/agents/answer-reviewer.md` |
| `.claude/settings.local.json` | подключает хуки `notes/hooks/protect-notes.sh` и `notes/hooks/block-git-writes.py` |

### `CLAUDE.local.md`

Claude Code читает его при старте сессии из корня проекта. Строка со знаком
`@` подставляет в контекст содержимое названного файла:

```markdown
@notes/claude/answer-rules.md
@notes/claude/common-rules.md
```

### Символические ссылки на правила кода, скиллы и агента

Правила с условием загрузки Claude Code ищет в `.claude/rules/`, скилл —
в `.claude/skills/`, агента — в `.claude/agents/`. Через импорт их
подключить нельзя: импорт загружает текст при старте сессии всегда,
а условие `paths`, команды `/explain` и `/setup-project` и отдельного агента с ограниченным
набором инструментов Claude Code берёт из файлов на этих местах. Ссылки
создаются из корня проекта:

```bash
mkdir -p .claude/rules .claude/skills .claude/agents
ln -s ../../notes/claude/code-rules.md .claude/rules/code-rules.md
ln -s ../../notes/claude/stack-rules.md .claude/rules/stack-rules.md
ln -s ../../notes/claude/skills/explain .claude/skills/explain
ln -s ../../notes/claude/skills/setup-project .claude/skills/setup-project
ln -s ../../notes/claude/agents/answer-reviewer.md .claude/agents/answer-reviewer.md
```

Путь внутри ссылки считается от папки, где она лежит, то есть от
`.claude/rules/`, `.claude/skills/` и `.claude/agents/`. Отсюда два `../..`:
они выводят в корень проекта.

### `.claude/settings.local.json`

Личный файл настроек Claude Code в проекте. Claude Code кладёт его поверх
общего `.claude/settings.json` проекта. Полный текст:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/notes/hooks/protect-notes.sh"
          },
          {
            "type": "command",
            "command": "python3 -I \"$CLAUDE_PROJECT_DIR\"/notes/hooks/block-git-writes.py"
          }
        ]
      }
    ]
  }
}
```

### Строки в `.gitignore` проекта

```gitignore
/CLAUDE.local.md
/.claude/agents
/.claude/skills
/.claude/rules
/notes
/backlog.md
```

`.claude/settings.local.json` в проекте игнорирует глобальный
`~/.config/git/ignore`, строка `**/.claude/settings.local.json`. Если
такой строки там нет, добавьте `/.claude/settings.local.json` в `.gitignore`
проекта.

## Хук `hooks/protect-notes.sh`

Claude Code запускает его перед каждой командой Bash в проекте. Хук
отказывает, если команда — `git clean` без `-n` или `--dry-run`, или если
команда удаления (`rm`, `rmdir`, `unlink`, `shred`, `find -delete`,
`rsync --delete`) упоминает `notes` или один из указателей. Список путей —
в переменной `TARGETS` внутри скрипта. Скрипт читает входные данные хука
через `jq`, так что `jq` должен быть установлен.

Ограничения:

- Хук проверяет только текст команды Bash. `rm -rf *` в корне проекта удалит
  `notes/`, но хук её пропустит: слова `notes` в тексте нет.
- Инструменты Write и Edit хук не проверяет: ими файл можно перезаписать.
  От этого защищает история git этого репозитория, но только для
  закоммиченного.

## Хук `hooks/block-git-writes.py`

Claude Code запускает его перед каждой командой Bash в проекте, после
`protect-notes.sh`. Хук отказывает, если команда вызывает git с действием,
которое меняет индекс, рабочие файлы, историю или ветку на GitHub: `add`,
`rm`, `mv`, `commit`, `push`, `pull`, `reset`, `restore`, `checkout`,
`switch`, `merge`, `rebase`, `cherry-pick`, `revert`, `am`, `apply`,
`stash`. Список — в переменной `BLOCKED` внутри скрипта. Чтение (`status`,
`log`, `diff`, `show`, `branch -a`, `fetch`) хук пропускает.

Зачем он нужен, если есть `permissions.deny` в `.claude/settings.json`
проекта. Правила `deny` вида `Bash(git commit *)` сравнивают начало
команды. `git -C notes commit …` начинается с `git -C` и проходит мимо них.
Так Claude уже однажды закоммитил в репозиторий заметок в прошлом проекте.

Как хук разбирает команду:

1. Текст heredoc (от `<<EOF` до строки `EOF`) — данные для программы,
   а не команды, и хук его убирает. Исключение — если текст читает
   `bash`, `sh`, `zsh` или `dash`: тогда хук проверяет его как команды.
2. Модуль Python `shlex` делит команду на слова с учётом кавычек. Поэтому
   `grep "git commit" файл` — это `grep` с одним аргументом, а не git.
3. Слова делятся на отдельные команды по `;`, `&&`, `||`, `|`, скобкам
   и переводу строки.
4. В каждой команде пропускаются `VAR=…` и обёртки (`sudo`, `env`,
   `timeout 10` …). Если дальше `git`, пропускаются его опции (`-C dir`,
   `-c k=v`, `--git-dir=…`), и следующее слово — действие.
5. Строка внутри `bash -c "…"`, `sh -c "…"` и `eval …` разбирается так же.

Скрипт на Python, а не на bash, из-за пункта 2: в bash нет готового
разбора команды на слова с учётом кавычек. Нужен `python3`; хук проверен
на Python 3.8.

Ограничения:

- Не ловит псевдонимы git (`git ci`), команды в скриптах из файлов
  и команду внутри строки в двойных кавычках (`echo "$(git commit)"`).
- Основная защита — правило Claude в памяти: эти команды он не выполняет.
  Хук — страховка от ошибки.

## Почему заметки не попадут в коммит проекта

- `/notes` в `.gitignore` проекта: `git add .` и `git add notes` в проекте
  папку пропускают.
- Claude не выполняет `git add`, `git commit`, `git push` и другие команды,
  которые меняют git. Их запрещают `permissions.deny` в
  `.claude/settings.json` проекта и хук `block-git-writes.py`.
- Обойти `.gitignore` может только `git add -f`. В проекте его не использовать.

## Как собрать всё заново

1. Склонировать проект, затем этот репозиторий в папку `notes/` внутри него.
2. Проверить, что строки из раздела про `.gitignore` есть в `.gitignore`
   проекта.
3. Создать в проекте `CLAUDE.local.md` и `.claude/settings.local.json`
   по тексту выше. Проверить, что git проекта игнорирует файл настроек:
   `git check-ignore -v .claude/settings.local.json`. Если не игнорирует,
   добавить строку `/.claude/settings.local.json` в `.gitignore` проекта.
4. Создать символические ссылки командами `ln -s` из раздела выше.
5. Проверить, что `protect-notes.sh` запускаемый:
   `chmod +x notes/hooks/protect-notes.sh`. `block-git-writes.py` запускается
   через `python3`, ему это не нужно. Проверить, что `python3` и `jq`
   установлены: `python3 --version`, `jq --version`.
6. Перезапустить сессию Claude Code: настройки, скиллы и агенты читаются
   при старте.
7. Убедиться:
   - `/context` показывает `CLAUDE.local.md` среди файлов памяти;
   - `/skills` показывает скиллы `explain` и `setup-project`;
   - `/agents` показывает агента `answer-reviewer`;
   - `/hooks` показывает два хука `PreToolUse`: `protect-notes.sh`
     и `block-git-writes.py`.

## Что переживает `git clean` в проекте

- `git clean -xdf` в проекте сносит все указатели, но папку `notes/` не
  трогает: git отказывается удалять вложенный репозиторий, пока не дашь `-f`
  дважды.
- `git clean -xdff` сносит и `notes/` вместе с её историей.

Поэтому единственная настоящая страховка — отправить историю этого
репозитория на закрытый удалённый репозиторий. Указатели после `-xdf`
восстанавливаются по этому README за пару минут.
