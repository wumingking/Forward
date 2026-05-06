import appui
import os
import time
import random
import threading

TARGETS_FILE = 'targets.txt'

api_id = 12345
api_hash = 'xxxxxxxx'


def load_targets(path):
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(
                '#填入需要签到的目标群组、bot的ID或用户名再重新运行脚本\n'
                '#ID或用户名与需要发送的文本或指令用|隔开\n'
                '#每行一个\n'
                '#下面为示例\n'
                '@bot|/checkin\n'
                '-1001234567890|签到\n'
            )
        return []
    result = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '|' not in line:
                continue
            tid_str, msg = line.split('|', 1)
            tid_str = tid_str.strip()
            msg = msg.strip()
            if not msg:
                continue
            tid = int(tid_str) if tid_str.lstrip('-').isdigit() else tid_str
            result.append({'id': str(tid), 'tid': tid, 'msg': msg})
    return result


def save_targets(path, targets):
    with open(path, 'w', encoding='utf-8') as f:
        for t in targets:
            f.write(str(t['tid']) + '|' + t['msg'] + '\n')


# ── State ──

state = appui.State(
    api_id_text=str(api_id),
    api_hash_text=api_hash,
    session_name='session',
    targets=[],
    logs=[],
    running=False,
    cancelled=False,
    new_target_text='',
)


def reload_targets():
    state.targets = load_targets(TARGETS_FILE)


def add_log(text):
    logs = list(state.logs)
    logs.append({'text': text, 'id': str(len(logs))})
    state.logs = logs


# ── Actions ──

def on_new_target_change(v):
    state.new_target_text = v


def on_add_target():
    text = state.new_target_text.strip()
    if not text:
        add_log('提示: 请输入签到目标')
        return
    if '|' not in text:
        add_log('格式错误: 需要用 | 分隔目标和指令，例如 @bot|/checkin')
        return
    tid_str, msg = text.split('|', 1)
    tid_str = tid_str.strip()
    msg = msg.strip()
    if not tid_str:
        add_log('格式错误: 目标ID不能为空')
        return
    if not msg:
        add_log('格式错误: 签到指令不能为空')
        return
    tid = int(tid_str) if tid_str.lstrip('-').isdigit() else tid_str
    targets = list(state.targets)
    targets.append({'id': str(tid), 'tid': tid, 'msg': msg})
    state.targets = targets
    try:
        save_targets(TARGETS_FILE, targets)
    except Exception as e:
        add_log('警告: 保存文件失败 — ' + str(e))
    state.new_target_text = ''
    add_log('已添加目标: ' + str(tid))


def on_delete_target(item_id):
    targets = list(state.targets)
    idx = None
    for i, t in enumerate(targets):
        if t['id'] == item_id:
            idx = i
            break
    if idx is not None:
        removed = targets.pop(idx)
        state.targets = targets
        try:
            save_targets(TARGETS_FILE, targets)
        except Exception:
            pass
        add_log('已删除: ' + removed['id'])


def on_start():
    if state.running:
        state.cancelled = True
        return

    if not state.api_id_text or not state.api_hash_text:
        add_log('错误: 请填写 API ID 和 API Hash')
        return

    if not state.targets:
        add_log('错误: 请先添加签到目标')
        return

    state.running = True
    state.cancelled = False
    add_log('开始签到...')

    def run_sign():
        try:
            from telethon.sync import TelegramClient
            from telethon.errors import FloodWaitError
        except ImportError:
            add_log('错误: 未安装 telethon，请先 pip install telethon')
            state.running = False
            return

        try:
            with TelegramClient(
                state.session_name,
                int(state.api_id_text),
                state.api_hash_text
            ) as client:
                add_log('已连接 Telegram')
                targets = list(state.targets)
                for i, t in enumerate(targets):
                    if state.cancelled:
                        break
                    try:
                        client.send_message(t['tid'], t['msg'])
                        add_log('[' + str(i + 1) + '] ' + t['id'] + ' 签到成功')
                        if i < len(targets) - 1 and not state.cancelled:
                            delay = random.randint(5, 10)
                            for _ in range(delay):
                                if state.cancelled:
                                    break
                                time.sleep(1)
                    except FloodWaitError as e:
                        add_log('限流 ' + str(e.seconds) + 's，等待中...')
                        for _ in range(min(e.seconds, 60)):
                            if state.cancelled:
                                break
                            time.sleep(1)
                    except Exception as e:
                        add_log('[' + str(i + 1) + '] ' + t['id'] + ' 失败: ' + str(e))

                if state.cancelled:
                    add_log('已取消')
                else:
                    add_log('全部完成')
        except Exception as e:
            add_log('连接失败: ' + str(e))

        state.running = False
        state.cancelled = False

    thread = threading.Thread(target=run_sign, daemon=True)
    thread.start()


# ── Load persisted targets ──

reload_targets()


# ── UI ──

def target_row(item):
    def on_del():
        on_delete_target(item['id'])

    return appui.HStack([
        appui.VStack([
            appui.Text(item['id']).font('headline'),
            appui.Text(item['msg']).font('caption').foreground_color('secondaryLabel'),
        ], alignment='leading'),
        appui.Spacer(),
        appui.Button('删除', action=on_del)
            .tint('systemRed')
            .button_style('plain'),
    ])


def log_row(item):
    return appui.Text(item['text']).font('caption')


def body():
    target_rows = [target_row(t) for t in state.targets] if state.targets else [
        appui.Text('暂无目标，请在上方添加').foreground_color('secondaryLabel'),
    ]

    log_section_content = [
        appui.ForEach(state.logs, row_builder=log_row, key='id'),
    ] if state.logs else [
        appui.Text('暂无日志').foreground_color('secondaryLabel'),
    ]

    return appui.NavigationStack(
        appui.List([
            appui.Section('配置', [
                appui.HStack([
                    appui.Text('API ID').font('subheadline')
                        .foreground_color('secondaryLabel')
                        .frame(width=72, alignment='leading'),
                    appui.TextField(
                        'API ID',
                        text=state.api_id_text,
                        on_change=lambda v: setattr(state, 'api_id_text', v),
                        keyboard_type='numberPad',
                    ),
                ]),
                appui.HStack([
                    appui.Text('API Hash').font('subheadline')
                        .foreground_color('secondaryLabel')
                        .frame(width=72, alignment='leading'),
                    appui.TextField(
                        'API Hash',
                        text=state.api_hash_text,
                        on_change=lambda v: setattr(state, 'api_hash_text', v),
                    ),
                ]),
                appui.HStack([
                    appui.Text('Session').font('subheadline')
                        .foreground_color('secondaryLabel')
                        .frame(width=72, alignment='leading'),
                    appui.TextField(
                        'Session',
                        text=state.session_name,
                        on_change=lambda v: setattr(state, 'session_name', v),
                    ),
                ]),
            ]),
            appui.Section('签到目标', [
                appui.HStack([
                    appui.TextField(
                        '格式: @bot|/checkin',
                        text=state.new_target_text,
                        on_change=on_new_target_change,
                    ).frame(max_width=appui.infinity),
                    appui.Button('添加', action=on_add_target)
                        .button_style('bordered_prominent')
                        .tint('systemBlue'),
                ]),
            ] + target_rows),
            appui.Section('操作', [
                appui.Button(
                    '停止' if state.running else '开始签到',
                    action=on_start,
                ).button_style('bordered_prominent')
                    .tint('systemRed' if state.running else 'systemGreen')
                    .frame(max_width=appui.infinity),
            ]),
            appui.Section('运行日志', log_section_content),
        ]).list_style('inset_grouped')
            .navigation_title('TG签到'),
    )


appui.run(body, state=state, presentation='fullscreen_with_close')
