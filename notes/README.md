# Заметки к проекту <имя проекта>

<!--
  БОЛВАНКА. Замените <имя проекта> и адреса репозиториев в угловых
  скобках, затем удалите этот комментарий.
-->

Этот репозиторий — личные заметки к проекту <имя проекта>
(`<адрес репозитория проекта>`). Он лежит внутри папки проекта, в подпапке
`notes/`.
В проекте эта папка указана в `.git/info/exclude`, поэтому в историю проекта из неё
не попадает ничего. Коммиты в заметки делаются отсюда, из `notes/`, и делает
их пользователь, а не Claude.

Удалённый репозиторий `notes/` (закрытый):
`<адрес репозитория notes/>`.

## Что здесь лежит

```
├── README.md                          ← этот файл
├── CLAUDE.md                          ← правила работы с папкой notes
├── backlog.md                         ← отложенные замечания
├── claude/
│   ├── answer-rules.md                ← правила ответов Claude
│   ├── common-rules.md                ← общие правила: владелец, трекер, git, поиск
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
этого репозитория. Все они указаны в `.git/info/exclude` проекта, и в историю проекта
не попадают. Пути в таблице — от корня проекта:

| Указатель в проекте | На что указывает |
|---|---|
| `CLAUDE.local.md` | импорт `notes/claude/answer-rules.md` и `notes/claude/common-rules.md` |
| `.claude/rules/code-rules.md` | символическая ссылка на `notes/claude/code-rules.md` |
| `.claude/rules/stack-rules.md` | символическая ссылка на `notes/claude/stack-rules.md` |
| `.claude/skills/explain` | символическая ссылка на `notes/claude/skills/explain` |
| `.claude/skills/setup-project` | символическая ссылка на `notes/claude/skills/setup-project` |
| `.claude/agents/answer-reviewer.md` | символическая ссылка на `notes/claude/agents/answer-reviewer.md` |
| `.claude/settings.local.json` | подключает хуки `notes/hooks/protect-notes.sh` и `notes/hooks/block-git-writes.py`, задаёт переменную окружения для команд Claude |

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
  "env": {
    "npm_config_update_notifier": "false"
  },
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

Ключ `env` задаёт переменные окружения. Claude Code передаёт их в каждую
команду, которую запускает. npm читает переменную `npm_config_<настройка>`
как свою настройку. Поэтому `npm_config_update_notifier=false` выключает
проверку новой версии npm на `registry.npmjs.org` во всех командах `npm`
и `npx` Claude. Без неё npm в песочнице проверяет версию при каждом
запуске: песочница не даёт ему прочитать `~/.npm`, где он хранит время
последней проверки. На команды в своём терминале переменная не влияет.
Команды проверки в `claude/stack-rules.md` вдобавок содержат флаг
`--no-update-notifier`: он выключает ту же проверку и виден в тексте.

### Строки в `.git/info/exclude` проекта

Папка `notes/` и указатели не должны попасть в git проекта, поэтому
git проекта их игнорирует. Строки для этого пишутся
в `.git/info/exclude`, а не в `.gitignore`. Git читает
`.git/info/exclude` так же, как `.gitignore`, но сам файл лежит в папке
`.git` клона и в коммит не попадает. Эти строки нужны только владельцу
заметок, для остальных программистов проекта они — лишняя информация.
Файл свой в каждом клоне, и строки добавляются в каждом новом клоне.

Команда выполняется из корня проекта. Она дописывает строки один раз:
если строка `/notes` в файле уже есть, команда ничего не меняет.
Claude её выполнить не может: запись в `.git` запрещают
`.claude/settings.json` и песочница.

```bash
mkdir -p .git/info
grep -qxF '/notes' .git/info/exclude 2>/dev/null || cat >> .git/info/exclude <<'EOF'

# personal Claude setup and private notes repository
/CLAUDE.local.md
/.claude/agents
/.claude/skills
/.claude/rules
/.claude/settings.local.json
/notes
EOF
```

Проверка:

```bash
git check-ignore -v CLAUDE.local.md notes .claude/settings.local.json
```

Команда выводит по строке на каждый путь, и в каждой строке стоит
`.git/info/exclude`.

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
Поэтому без хука Claude может закоммитить в репозиторий `notes/`, хотя
правило `deny` это запрещает.

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

- `/notes` в `.git/info/exclude` проекта: `git add .` и `git add notes` в проекте
  папку пропускают.
- Claude не выполняет `git add`, `git commit`, `git push` и другие команды,
  которые меняют git. Их запрещают `permissions.deny` в
  `.claude/settings.json` проекта и хук `block-git-writes.py`.
- Обойти игнорирование может только `git add -f`. В проекте его не использовать.

## Как собрать всё заново

Порядок для того, у кого есть репозиторий проекта и этот репозиторий,
но нет файлов в корне проекта, которые на него указывают. Например,
для программиста, которому передали заметки.

1. Проверить программы. Claude Code должен быть установлен:
   в VS Code или редакторе на его основе (Cursor и другие) — расширение
   Claude Code, в консоли — консольная версия. Как установить —
   https://code.claude.com/docs/en/setup. Остальные программы проверить
   командами:

   ```bash
   git --version
   python3 --version
   jq --version
   ```

   Каждая команда выводит номер версии. Если вместо версии пришло
   `command not found`, программы нет. Зачем каждая программа:
   - `git` — клонирует оба репозитория;
   - `python3` — запускает хук `block-git-writes.py`. Хук проверен
     на Python 3.8;
   - `jq` — читает входные данные хука `protect-notes.sh`. Без `jq` хук
     пропускает любую команду удаления.

   Недостающие установить. В Ubuntu и Debian — одной командой
   `sudo apt install git python3 jq`, в других системах — их менеджером
   пакетов.
2. Склонировать проект, затем этот репозиторий в папку `notes/` внутри него.
3. Добавить строки в `.git/info/exclude` проекта и проверить их
   командами из раздела «Строки в `.git/info/exclude` проекта».
4. Создать в проекте `CLAUDE.local.md` и `.claude/settings.local.json`
   по тексту выше.
5. Создать символические ссылки командами `ln -s` из раздела выше.
6. Включить хук `pre-commit` проекта, если в проекте есть папка
   `.githooks/`. Команда — в README проекта.
7. Проверить, что `protect-notes.sh` запускаемый:
   `chmod +x notes/hooks/protect-notes.sh`. `block-git-writes.py` запускается
   через `python3`, ему это не нужно.
8. Перезапустить сессию Claude Code: настройки, скиллы и агенты читаются
   при старте.
9. Убедиться:
   - `/context` показывает `CLAUDE.local.md` среди файлов памяти;
   - `/skills` показывает скиллы `explain` и `setup-project`;
   - `/agents` показывает агента `answer-reviewer`;
   - `/hooks` показывает два хука `PreToolUse`: `protect-notes.sh`
     и `block-git-writes.py`.

   В панели расширения VS Code `/skills` работает так же, а хуки видны
   в меню Customize, раздел Hooks. Есть ли в панели `/context`
   и `/agents`, документация не говорит, и это не проверено. Если
   после ввода `/` их нет в списке, эти две проверки делаются
   в консольной версии.
10. Если заметки переданы от другого программиста, запустить
    `/setup-project читатель`. Скилл заменит раздел «Читатель»
    в `claude/answer-rules.md` и строку «Владелец заметок»
    в `claude/common-rules.md`. Потом снова перезапустить сессию:
    оба файла загружаются при старте.

## Что переживает `git clean` в проекте

- `git clean -xdf` в проекте сносит все указатели, но папку `notes/` не
  трогает: git отказывается удалять вложенный репозиторий, пока не дашь `-f`
  дважды.
- `git clean -xdff` сносит и `notes/` вместе с её историей.

Поэтому единственная настоящая страховка — отправить историю этого
репозитория на закрытый удалённый репозиторий. Указатели после `-xdf`
восстанавливаются по этому README за пару минут.
