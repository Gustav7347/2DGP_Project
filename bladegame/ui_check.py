"""SDL menu-path checks with explicit reward/death fixtures; not a playthrough."""
import ctypes


class UICheck:
    def __init__(self):
        self.seen={key:False for key in ('mouse_hover','help','settings','volume','mute','shake','hints','start','help_pauses','help_returns','mouse_settings','reward_help','reward_modal','reward_number','reward_enter','reward_return','reward_keyboard','result_title','mouse_start')}

    def feed(self,frame,sdl):
        if frame==1:
            event=sdl.SDL_Event();event.type=sdl.SDL_MOUSEMOTION
            event.motion.x=300;event.motion.y=720-325;sdl.SDL_PushEvent(ctypes.byref(event))
        keys={2:'DOWN',4:'RETURN',8:'ESCAPE',10:'DOWN',12:'DOWN',14:'RETURN',18:'LEFT',
              20:'DOWN',22:'RETURN',24:'DOWN',26:'RETURN',28:'DOWN',30:'RETURN',34:'ESCAPE',38:'RETURN',
              44:'F1',48:'ESCAPE',52:'ESCAPE',60:'ESCAPE',64:'RETURN',90:'F1',91:'RIGHT',92:'2',93:'RETURN',94:'F1',95:'ESCAPE',96:'RIGHT',98:'RETURN',110:'t'}
        if frame in keys:
            for kind in (sdl.SDL_KEYDOWN,sdl.SDL_KEYUP):
                event=sdl.SDL_Event();event.type=kind;event.key.keysym.sym=getattr(sdl,'SDLK_'+keys[frame]);event.key.repeat=0
                sdl.SDL_PushEvent(ctypes.byref(event))
        clicks={56:(640,291),91:(640,350),114:(300,325)}
        if frame in clicks:
            x,y=clicks[frame]
            for kind in (sdl.SDL_MOUSEBUTTONDOWN,sdl.SDL_MOUSEBUTTONUP):
                event=sdl.SDL_Event();event.type=kind;event.button.button=sdl.SDL_BUTTON_LEFT
                event.button.x=x;event.button.y=720-y;sdl.SDL_PushEvent(ctypes.byref(event))
        if frame==124:
            event=sdl.SDL_Event();event.type=sdl.SDL_QUIT;sdl.SDL_PushEvent(ctypes.byref(event))

    def observe(self,frame,game,renderer):
        ui=renderer.ui
        checks={1:('mouse_hover',game.state=='title' and ui.page=='main' and ui.focus==0),
                4:('help',ui.page=='help'),14:('settings',ui.page=='settings'),18:('volume',abs(renderer.volume-.1)<1e-8),
                22:('mute',renderer.muted),26:('shake',not renderer.shake_enabled),30:('hints',not renderer.hints_enabled),
                38:('start',game.state=='playing'),44:('help_pauses',game.state=='paused' and ui.page=='help'),
                48:('help_returns',game.state=='playing' and ui.page=='main'),56:('mouse_settings',ui.page=='settings'),
                90:('reward_help',game.state=='reward' and ui.page=='help'),
                91:('reward_modal',game.state=='reward' and ui.reward_focus==0),
                92:('reward_number',game.state=='reward' and ui.page=='help' and ui.reward_focus==0),
                93:('reward_enter',game.state=='reward' and ui.page=='main' and ui.reward_focus==0),
                95:('reward_return',game.state=='reward' and ui.page=='main'),
                98:('reward_keyboard',game.stage_index==1 and game.player.style=='moon'),110:('result_title',game.state=='title'),
                114:('mouse_start',game.state=='playing' and game.stage_index==0)}
        if frame in checks:
            name,result=checks[frame];self.seen[name]=result
        if frame==89:
            game.state='reward';game.stage_index=0;game.choices=['blood','moon','chain'];ui.reward_focus=0
        if frame==105:
            game._hurt_player(9999,ignore_invulnerability=True);game.player.action_time=1.

    def verify(self):
        if not all(self.seen.values()):raise AssertionError(self.seen)
        return self.seen
