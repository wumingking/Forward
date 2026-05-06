import appui
import haptics
import storage

WORK = 25 * 60
REST = 5 * 60
sessions_total = storage.get_int('focus_total', 0)

state = appui.State(
    left=WORK,
    running=False,
    resting=False,
    done=sessions_total,
)
_timer = [None]

def tick():
    if state.left > 0:
        state.left -= 1
    else:
        if _timer[0] and _timer[0].is_running:
            _timer[0].stop()
        state.running = False
        haptics.notification('success')
        if state.resting:
            state.resting = False
            state.left = WORK
        else:
            state.done += 1
            storage.set_int('focus_total', state.done)
            state.resting = True
            state.left = REST

_timer[0] = appui.Timer(interval=1.0, action=tick)

def toggle():
    def _do():
        if state.running:
            if _timer[0]:
                _timer[0].stop()
            state.running = False
            haptics.impact('light')
        else:
            if _timer[0]:
                _timer[0].start()
            state.running = True
            haptics.impact('medium')
    appui.animate(_do, type='spring')

def reset():
    def _do():
        if _timer[0] and _timer[0].is_running:
            _timer[0].stop()
        state.running = False
        state.resting = False
        state.left = WORK
        haptics.impact('light')
    appui.animate(_do, type='spring')

def stat_box(value, label, color):
    return appui.VStack([
        appui.Text(value).font("title2").bold().foreground_color(color),
        appui.Text(label).font("caption").foreground_color('#8E8E93'),
    ], spacing=2)

def body():
    total = REST if state.resting else WORK
    progress = 1.0 - state.left / total if total else 0
    m, s = divmod(state.left, 60)
    accent = '#FF6B6B' if state.resting else '#5B7FFF'

    sz = 260
    c = sz / 2
    r = 105
    ctx = appui.DrawingContext()
    ctx.arc(c, c, r, 0, 360, color='#E8E8ED', line_width=14)
    if progress > 0.002:
        ctx.arc(c, c, r, -90, -90 + progress * 360,
                color=accent, line_width=14)

    phase = '\u4f11\u606f\u4e2d' if state.resting else (
        '\u4e13\u6ce8\u4e2d' if state.running else '\u51c6\u5907\u5f00\u59cb')

    return appui.NavigationStack(
        appui.VStack([
            appui.Spacer(),
            appui.Text(phase).font("headline")
                .foreground_color('#8E8E93'),
            appui.ZStack([
                appui.Canvas(width=sz, height=sz, context=ctx),
                appui.VStack([
                    appui.Text(f'{m:02d}:{s:02d}')
                        .font("system", size=54, weight="ultralight")
                        .foreground_color(accent),
                    appui.Text('5 \u5206\u949f\u4f11\u606f' if state.resting else '25 \u5206\u949f\u4e13\u6ce8')
                        .font("caption").foreground_color('#AEAEB2'),
                ], spacing=4),
            ]),
            appui.Spacer().frame(height=36),
            appui.HStack([
                appui.Button('\u91cd\u7f6e', action=reset)
                    .button_style('bordered').tint('#AEAEB2'),
                appui.Spacer().frame(width=20),
                appui.Button('\u6682\u505c' if state.running else '\u5f00\u59cb',
                             action=toggle)
                    .button_style('bordered_prominent').tint(accent),
            ]),
            appui.Spacer().frame(height=40),
            appui.HStack([
                stat_box(str(state.done), '\u6b21\u4e13\u6ce8', accent),
                appui.Spacer(),
                stat_box(str(state.done * 25), '\u5206\u949f', accent),
            ]).frame(max_width=220),
            appui.Spacer(),
        ], spacing=10)
        .navigation_title('\u4e13\u6ce8\u8ba1\u65f6')
    )

appui.run(body, state=state, presentation='fullscreen_with_close')
