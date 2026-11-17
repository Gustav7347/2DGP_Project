"""Shared mouse/keyboard menu behavior; independent of SDL drawing."""
from . import config as C


class Interface:
    def __init__(self):
        self.page='main'
        self.focus=0
        self.reward_focus=0
        self.resume_after_help=False
        self.settings_status='설정은 다음 실행에도 유지됩니다.'

    @staticmethod
    def card_at(x,y):
        if not 180<=y<=500:return -1
        for i in range(3):
            if 100+i*370<=x<=440+i*370:return i
        return -1

    def buttons(self,game):
        if game.state=='dead' and not game.result_visible:return []
        if self.page=='help':return [('back','돌아가기',440,88,400,52)]
        if self.page=='settings':
            labels=[('volume','효과음'),('mute','음소거'),('shake','화면 흔들림'),('hints','처음 조작 안내'),('back','돌아가기')]
            return [(a,b,390,440-i*68,500,52) for i,(a,b) in enumerate(labels)]
        if game.state=='title':
            labels=[('start','도장으로 향한다'),('help','조작과 전투'),('settings','설정'),('quit','게임 종료')]
            return [(a,b,100,300-i*62,490,50) for i,(a,b) in enumerate(labels)]
        if game.state=='paused':
            labels=[('resume','계속하기'),('help','조작과 전투'),('settings','설정'),('restart','처음부터'),('title','제목 화면')]
        elif game.state in ('dead','clear'):
            labels=[('start','다시 도전한다'),('title','제목 화면')]
        else:return []
        top=390 if game.state=='paused' else 205
        return [(a,b,430,top-i*62,420,50) for i,(a,b) in enumerate(labels)]

    def button_at(self,game,x,y):
        for i,(_,_,bx,by,w,h) in enumerate(self.buttons(game)):
            if bx<=x<=bx+w and by<=y<=by+h:return i
        return -1

    def hover(self,game,x,y):
        if game.state=='reward' and self.page=='main':
            index=self.card_at(x,y)
            if index>=0:self.reward_focus=index
        else:
            index=self.button_at(game,x,y)
            if index>=0:self.focus=index

    def open_help(self,game):
        if self.page=='help':self.back(game);return
        self.resume_after_help=game.state=='playing'
        if self.resume_after_help:game.toggle_pause()
        self.page='help';self.focus=0

    def back(self,game):
        self.page='main';self.focus=0
        if self.resume_after_help and game.state=='paused':game.toggle_pause()
        self.resume_after_help=False

    def activate(self,game,renderer,index=None,adjust=1):
        buttons=self.buttons(game)
        if not buttons:return True
        index=self.focus if index is None else index
        if not 0<=index<len(buttons):return True
        if not getattr(renderer,'muted',True) and 'reward' in getattr(renderer,'sounds',{}):
            renderer.play_sound('reward')
        action=buttons[index][0]
        if action in ('start','restart'):
            game.start();self.page='main';self.focus=self.reward_focus=0
        elif action=='resume':game.toggle_pause();self.focus=0
        elif action=='title':game.state='title';self.page='main';self.focus=0
        elif action=='help':self.open_help(game)
        elif action=='settings':self.page='settings';self.focus=0
        elif action=='back':self.back(game)
        elif action=='volume':renderer.set_volume(.05*adjust)
        elif action=='mute':renderer.toggle_mute()
        elif action=='shake':renderer.shake_enabled=not renderer.shake_enabled
        elif action=='hints':renderer.hints_enabled=not renderer.hints_enabled
        return action!='quit'

    def focus_lost(self,game):
        if game.state=='playing':game.toggle_pause();self.page='main';self.focus=0


def combat_status(player):
    """Keep the expiring survival timer visible alongside a prepared attack."""
    if player.counter_ready:
        ready='육참골단 준비'+(' · 간파' if player.insight else '')
        return f'불굴 {player.unyielding_left:.1f}초 · '+ready if player.unyielding_left>0 else ready
    if player.unyielding_left>0:
        timer=f'불굴 {player.unyielding_left:.1f}초'
        return timer+' · 간파' if player.insight else timer
    if player.insight:return '간파 준비'
    return '사용함' if not player.heals else ''


def choice_detail(key,player):
    """Player-facing numbers and tradeoffs derived from actual game balance."""
    if key=='blood':return [f'최대 피해 ×{1+C.BLOOD_BONUS:.1f}', '체력이 낮을수록 강해진다', '위험을 감수하는 전투']
    if key=='moon':return [f'패링마다 체력 +{C.MOON_HEAL:g}',f'일반 적 기절 · 보스 {C.BOSS_PARRIES}회 누적','타이밍으로 흐름을 되찾는다']
    if key=='chain':return [f'적중마다 +{C.CHAIN_BONUS*100:g}% · 최대 {C.CHAIN_CAP}중첩',f'{C.CHAIN_GRACE:g}초 미적중 후 초당 {C.CHAIN_DECAY:g} 감소','공격을 이어갈수록 강해진다']
    if key=='counter':return [f'피해를 받고 다음 공격 ×{C.COUNTER_DAMAGE:g}','강화 1회 저장 · 공격 시작 시 소모','반월 회복보다 피해가 먼저 적용']
    if key=='echo':return [f'본타·잔영 각각 원래 피해의 {C.ECHO_DAMAGE*100:g}%',f'{C.ECHO_DELAY:g}초 뒤 같은 위치에 재타격','혈흔과 연결: 두 번의 출혈 갱신' if 'bleed' in player.augments else '연참과 연결: 적중 중첩을 두 번' if player.style=='chain' else '잔영도 적에게 닿아야 피해 적용']
    if key=='bleed':return [f'{C.BLEED_TIME:g}초 출혈 · 초당 피해 {C.BLEED_DPS:g}','패링 시 남은 출혈 피해 즉시 적용','패링과 적중을 함께 활용']
    if key=='insight':return [f'다음 공격 피해 ×{C.INSIGHT_DAMAGE:g}',f'패링 후 공격 범위 ×{C.INSIGHT_RANGE:g}','다음 한 번의 공격에 소모']
    if key=='unyielding':return [f'체력 1로 {C.UNYIELDING_TIME:g}초 버티기',f'버티는 동안 피해 +{C.UNYIELDING_BONUS*100:g}%','한 판 1회 · 회생보다 먼저 발동']
    if key=='revive':return ['치명상 무시 · 전체 체력 회복','한 판 1회 · 스테이지 간 소모 유지','불굴의 보호가 끝난 뒤 발동']
    return []


def reward_sections(key,player):
    """Short comparable card copy; F1 keeps the fuller choice_detail numbers."""
    values={
        'blood':(f'피해 최대 ×{1+C.BLOOD_BONUS:.1f}','잃은 체력에 비례해 강화','회복하면 증가량도 감소'),
        'moon':(f'패링 시 체력 +{C.MOON_HEAL:g}','정면 패링 성공 시 발동',f'일반 적 기절 · 보스 {C.BOSS_PARRIES}회'),
        'chain':(f'적중마다 피해 +{C.CHAIN_BONUS*100:g}%',f'최대 {C.CHAIN_CAP}중첩까지 누적',f'{C.CHAIN_GRACE:g}초 미적중 후 점차 감소'),
        'counter':(f'다음 공격 피해 ×{C.COUNTER_DAMAGE:g}','패링 성공 후 강화 준비','피해를 받음 · 1회만 저장'),
        'echo':(f'본타·잔영 각각 {C.ECHO_DAMAGE*100:g}%',f'공격 후 {C.ECHO_DELAY:g}초 뒤 재타격','같은 위치 · 잔영 재생성 없음'),
        'bleed':(f'{C.BLEED_TIME:g}초간 초당 피해 {C.BLEED_DPS:g}','공격 적중 시 출혈 부여','패링하면 남은 출혈 정산'),
        'insight':(f'다음 공격 피해 ×{C.INSIGHT_DAMAGE:g}','정면 패링 성공 시 준비',f'1회 소모 · 범위 ×{C.INSIGHT_RANGE:g}'),
        'unyielding':(f'체력 1로 {C.UNYIELDING_TIME:g}초 생존','치명상에서 발동 · 피해 증가','한 판 1회 · 회생보다 우선'),
        'revive':('치명상 무시 · 전체 회복','치명상에서 발동','한 판 1회 · 불굴보다 나중')}
    return list(zip(('효과','조건','제약'),values[key]))


def last_hit_text(hit):
    names={'sword':'검사','spear':'창병','boss':'도장주'}
    if not hit or hit['enemy_kind'] not in names:return '마지막 피격 정보 없음'
    tips={'behind':'뒤쪽 적에게 피격 · 적을 바라보고 패링',
          'window_ended':'패링 유효시간이 지난 뒤 피격 · 타격 직전에 입력',
          'spent':'이번 패링을 이미 사용한 뒤 피격 · 다음 예고 확인',
          'counter_cost':'육참골단은 패링해도 피해를 받음 · 남은 체력 확인',
          'unblocked':'패링 방어가 없는 상태로 피격 · 예고와 회복약 확인'}
    attack={'slash':'베기','thrust':'찌르기'}.get(hit['attack'],'공격')
    return f'마지막 피격  {names[hit["enemy_kind"]]} · {attack} / '+tips.get(hit['reason'],'피격 당시 상태를 확인하세요')
