from dataclasses import dataclass


@dataclass
class LooksBlocks:
    looks_sayforsecs: str = "looks_sayforsecs"
    looks_say: str = "looks_say"
    looks_thinkforsecs: str = "looks_thinkforsecs"
    looks_think: str = "looks_think"
    looks_switchcostumeto: str = "switchcostumeto"
    looks_nextcostume: str = "looks_nextcostume"
    looks_switchbackdropto: str = "looks_switchbackdropto"
    looks_setsizeto: str = "looks_setsizeto"
    looks_changeeffectby: str = "looks_changeeffectby"
    looks_seteffectto: str = "looks_seteffectto"
    looks_cleargraphiceffects: str = "looks_cleargraphiceffects"
    looks_show: str = "looks_show"
    looks_hide: str = "looks_hide"


@dataclass
class MotionBlocks:
    motion_movestpes: str = "motion_movesteps"
    motion_turnright: str = "motion_turnright"
    motion_turnleft: str = "motion_turnleft"
    motion_goto: str = "motion_goto"
    motion_goto_menu: str = "motion_goto_menu"
    motion_gotoxy: str = "motion_gotoxy"
    motion_glideto: str = "motion_glideto"
    motion_glidesecstoxy: str = "motion_glidesecstoxy"
    motion_pointtowards: str = "motion_pointtowards"
    motion_changexby: str = "motion_changexby"
    motion_setx: str = "motion_setx"
    motion_changeyby: str = "motion_changeyby"
    motion_sety: str = "motion_sety"
    motion_ifonedgebounce: str = "motion_ifonedgebounce"
    motion_setrotationstyle: str = "motion_setrotationstyle"


@dataclass
class SoundBlocks:
    sound_playuntildone: str = "sound_playuntildone"  # special, iLUGzp;sGdtbe4%[H7M+_sound_playuntildone
    sound_play: str = "sound_play"  # iLUGzp;sGdtbe4%[H7M+_sound_play
    sound_stopallsounds: str = "sound_stopallsounds"
    sound_changeeffectby: str = "sound_changeeffectby"
    sound_seteffectto: str = "sound_seteffectto"
    sound_cleareffects: str = "sound_cleareffects"
    sound_changevolumeby: str = "sound_changevolumeby"
    sound_setvolumeto: str = "sound_setvolumeto"


@dataclass
class EventsBlocks:
    event_whenflagclicked: str = "event_whenflagclicked"
    event_whenkeypressed: str = "event_whenkeypressed"
    event_whenthisspriteclicked: str = "event_whenthisspriteclicked"
    event_whenbackdropswitchesto: str = "event_whenbackdropswitchesto"
    event_whengreaterthan: str = "event_whengreaterthan"
    event_whenbroadcastreceived: str = "event_whenbroadcastreceived"
    event_broadcast: str = "event_broadcast"
    event_broadcastandwait: str = "event_broadcastandwait"


@dataclass
class ControlBlocks:
    control_wait: str = "control_wait"
    control_repeat: str = "control_repeat"
    forever: str = "forever"
    control_if: str = "control_if"
    control_if_else: str = "control_if_else"
    wait_until: str = "wait_until"
    repeat_until: str = "repeat_until"
    control_stop: str = "control_stop"
    control_start_as_clone: str = "control_start_as_clone"
    control_create_clone_of: str = "control_create_clone_of"
    control_delete_this_clone: str = "control_delete_this_clone"

@dataclass
class SensingBlocks:
    sensing_touchingobject: str = "sensing_touchingobject"
    sensing_touchingcolor: str = "sensing_touchingcolor"
    sensing_coloristouchingcolor: str = "sensing_coloristouchingcolor"
    sensing_distanceto: str = "sensing_distanceto"
    askandwait: str = "askandwait"
    sensing_keypressed: str = "sensing_keypressed"


@dataclass
class AssembleBlocks:
    motion_blocks: MotionBlocks
    look_blocks: LooksBlocks
    sound_blocks: SoundBlocks
    events_blocks: EventsBlocks
    control_blocks: ControlBlocks
    sensing_blocks: SensingBlocks