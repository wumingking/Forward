import appui
import haptics
import storage
import json

default_list = ['\u65e9\u8d77\u8fd0\u52a8', '\u9605\u8bfb 30 \u5206\u949f', '\u559d 8 \u676f\u6c34', '\u5192\u60f3 10 \u5206\u949f', '\u5199\u65e5\u8bb0']
saved = storage.get('habits_v2', None)
try:
    habits_init = json.loads(saved) if saved else list(default_list)
    if not isinstance(habits_init, list):
        habits_init = list(default_list)
except Exception:
    habits_init = list(default_list)
try:
    done_init = json.loads(storage.get('done_today', '[]'))
    if not isinstance(done_init, list):
        done_init = []
except Exception:
    done_init = []

state = appui.State(
    habits=habits_init,
    done=done_init,
    new_name='',
)

def save():
    storage.set('habits_v2', json.dumps(state.habits))
    storage.set('done_today', json.dumps(state.done))

def toggle(name):
    def _do():
        d = list(state.done)
        if name in d:
            d.remove(name)
        else:
            d.append(name)
            haptics.notification('success')
        state.done = d
        save()
    appui.animate(_do, type='spring')

def add_habit():
    n = state.new_name.strip()
    if n and n not in state.habits:
        h = list(state.habits)
        h.append(n)
        state.habits = h
        state.new_name = ''
        save()
        haptics.impact('light')

def remove_habit(name):
    h = list(state.habits)
    if name in h:
        h.remove(name)
    state.habits = h
    d = list(state.done)
    if name in d:
        d.remove(name)
    state.done = d
    save()

def set_new_name(v):
    state.new_name = v

def habit_row(h):
    is_done = h in state.done
    icon = 'checkmark.circle.fill' if is_done else 'circle'
    color = '#34C759' if is_done else '#D1D1D6'
    return appui.HStack([
        appui.Image(system_name=icon)
            .foreground_color(color).font("title3"),
        appui.Text(h).strikethrough(is_done)
            .foreground_color('#AEAEB2' if is_done else '#1C1C1E'),
        appui.Spacer(),
    ], spacing=12).on_tap(lambda name=h: toggle(name))

def today_tab():
    total = len(state.habits)
    done_count = sum(1 for h in state.habits if h in state.done)
    pct = int(done_count / total * 100) if total else 0
    return appui.NavigationStack(
        appui.List([
            appui.Section([
                appui.HStack([
                    appui.VStack([
                        appui.Text(f'{done_count}/{total}')
                            .font("title").bold(),
                        appui.Text('\u4eca\u65e5\u5b8c\u6210')
                            .font("caption").foreground_color('#8E8E93'),
                    ], spacing=2),
                    appui.Spacer(),
                    appui.Gauge(value=done_count / total if total else 0,
                                label=f'{pct}%')
                        .frame(width=56, height=56).tint('#34C759'),
                ]),
            ]),
            appui.Section([
                appui.ForEach(state.habits,
                              row_builder=habit_row,
                              key=lambda h: h),
            ], header='\u4e60\u60ef\u5217\u8868'),
        ]).navigation_title('\u4eca\u65e5\u6253\u5361')
    )

def chart_tab():
    total = len(state.habits)
    done_count = sum(1 for h in state.habits if h in state.done)
    w, h = 320, 200
    ctx = appui.DrawingContext()
    ctx.rounded_rect(0, 0, w, h, 16, color='#F2F2F7', fill=True)
    if total > 0:
        bw = max(4, min(32, (w - 40) / total - 8))
        gap = max(2, (w - bw * total) / (total + 1))
        mh = h - 56
        for i, name in enumerate(state.habits):
            x = gap + i * (bw + gap)
            ok = name in state.done
            bh = mh if ok else mh * 0.12
            c = '#34C759' if ok else '#E5E5EA'
            y = h - 28 - bh
            ctx.rounded_rect(x, y, bw, bh, bw / 2, color=c, fill=True)
            ctx.fill_text(name[:2], x + 2, h - 16, color='#8E8E93',
                          font_size=10)
    return appui.NavigationStack(
        appui.VStack([
            appui.Text(f'\u4eca\u65e5\u5b8c\u6210 {done_count}/{total}')
                .font("headline").padding(),
            appui.Canvas(width=w, height=h, context=ctx),
            appui.Spacer(),
        ], spacing=16).navigation_title('\u7edf\u8ba1')
    )

def settings_tab():
    return appui.NavigationStack(
        appui.Form([
            appui.Section([
                appui.HStack([
                    appui.TextField(placeholder='\u65b0\u4e60\u60ef\u540d\u79f0',
                                    text=state.new_name,
                                    on_change=set_new_name),
                    appui.Button('\u6dfb\u52a0', action=add_habit)
                        .button_style('bordered_prominent')
                        .tint('#5856D6'),
                ]),
            ], header='\u6dfb\u52a0\u4e60\u60ef'),
            appui.Section([
                appui.ForEach(
                    state.habits,
                    row_builder=lambda h: appui.HStack([
                        appui.Text(h),
                        appui.Spacer(),
                        appui.Button('\u5220\u9664',
                                     action=lambda name=h: remove_habit(name))
                            .foreground_color('red').font("caption"),
                    ]),
                    key=lambda h: h,
                ),
            ], header=f'{len(state.habits)} \u4e2a\u4e60\u60ef'),
        ]).navigation_title('\u8bbe\u7f6e')
    )

def body():
    return appui.TabView([
        appui.Tab(title='\u4eca\u65e5', system_image='checkmark.circle.fill',
                  content=today_tab()),
        appui.Tab(title='\u7edf\u8ba1', system_image='chart.bar.fill',
                  content=chart_tab()),
        appui.Tab(title='\u8bbe\u7f6e', system_image='gearshape.fill',
                  content=settings_tab()),
    ])

appui.run(body, state=state, presentation='fullscreen_with_close')
