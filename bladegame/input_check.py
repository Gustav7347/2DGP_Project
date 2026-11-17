"""SDL event-queue smoke driver, used only with --input-check."""
import ctypes


class InputCheck:
    def __init__(self):
        self.seen={'start':False,'move':False,'jump':False,'combo':False,'parry':False,'pause':False,'restart':False,
                   'arrow_left':False,'arrow_right':False,'held_single':False}

    def feed(self, frame, sdl):
        if frame==1:
            # Prime the start item through normal hover; native startup motion can select another item.
            event=sdl.SDL_Event();event.type=sdl.SDL_MOUSEMOTION
            event.motion.x=300;event.motion.y=720-325;sdl.SDL_PushEvent(ctypes.byref(event))
        keys={2:('down','RETURN'),3:('up','RETURN'),10:('down','d'),20:('down','SPACE'),21:('up','SPACE'),
              130:('up','d'),140:('down','ESCAPE'),141:('up','ESCAPE'),155:('down','ESCAPE'),156:('up','ESCAPE'),
              170:('down','ESCAPE'),171:('up','ESCAPE'),175:('down','r'),176:('up','r'),
              181:('down','LEFT'),187:('up','LEFT'),191:('down','RIGHT'),203:('up','RIGHT')}
        if frame in keys:
            action,key=keys[frame]
            event=sdl.SDL_Event()
            event.type=sdl.SDL_KEYDOWN if action=='down' else sdl.SDL_KEYUP
            event.key.keysym.sym=getattr(sdl,'SDLK_'+key)
            event.key.repeat=0
            sdl.SDL_PushEvent(ctypes.byref(event))
        buttons={28:(True,sdl.SDL_BUTTON_LEFT),65:(False,sdl.SDL_BUTTON_LEFT),
                 66:(True,sdl.SDL_BUTTON_LEFT),67:(False,sdl.SDL_BUTTON_LEFT),
                 80:(True,sdl.SDL_BUTTON_LEFT),81:(False,sdl.SDL_BUTTON_LEFT),
                 100:(True,sdl.SDL_BUTTON_LEFT),101:(False,sdl.SDL_BUTTON_LEFT),
                 122:(True,sdl.SDL_BUTTON_RIGHT),123:(False,sdl.SDL_BUTTON_RIGHT)}
        if frame in buttons:
            down,button=buttons[frame]
            event=sdl.SDL_Event()
            event.type=sdl.SDL_MOUSEBUTTONDOWN if down else sdl.SDL_MOUSEBUTTONUP
            event.button.button=button; event.button.x=600; event.button.y=350
            sdl.SDL_PushEvent(ctypes.byref(event))
        if frame==205:
            event=sdl.SDL_Event(); event.type=sdl.SDL_QUIT
            sdl.SDL_PushEvent(ctypes.byref(event))

    def observe(self, frame, game):
        p=game.player
        if game.state=='playing': self.seen['start']=True
        if p.x>220: self.seen['move']=True
        if p.y>140: self.seen['jump']=True
        if p.combo_index==2: self.seen['combo']=True
        if frame==64:self.seen['held_single']=sum(e['kind']=='attack' for e in game.events)==1 and p.combo_index==0
        if p.action=='parry': self.seen['parry']=True
        if game.state=='paused': self.seen['pause']=True
        if frame>175 and game.state=='playing' and p.x==160 and p.hp==100: self.seen['restart']=True
        if frame==185 and p.x<160:self.seen['arrow_left']=True
        if frame==201 and p.x>160:self.seen['arrow_right']=True

    def verify(self):
        if not all(self.seen.values()): raise AssertionError(self.seen)
        return self.seen
