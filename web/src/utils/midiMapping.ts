// Full CC Mapping for MG-400 Web MIDI
export const MIDI_CC_MAP: Record<string, number> = {
    exp_toe_switch: 0,
    cmp_enable: 1, efx_enable: 2, amp_enable: 3, eq_enable: 4,
    nr_enable: 5, mod_enable: 6, dly_enable: 7, rvb_enable: 8,
    cab_enable: 9, p_l: 10, mic_enable: 11,

    cmp_knob_1: 14, cmp_knob_2: 15, cmp_knob_3: 16, cmp_knob_4: 17,
    efx_knob_1: 18, efx_knob_2: 19, efx_knob_3: 20, efx_knob_4: 21, efx_knob_5: 22, efx_knob_6: 23,

    amp_knob_1: 24, gain: 24, amp_gain: 24,
    amp_knob_2: 25, master: 25, amp_master: 25,
    amp_knob_3: 26, bass: 26, amp_bass: 26,
    amp_knob_4: 27, mid: 27, amp_mid: 27,
    amp_knob_5: 28, treble: 28, amp_treble: 28,
    amp_knob_6: 29, presence: 29, amp_presence: 29,
    amp_knob_7: 30, amp_knob_8: 31,

    eq_knob_1: 32, eq_low: 32, eq_knob_2: 33, eq_mid_low: 33,
    eq_knob_3: 34, eq_mid: 34, eq_knob_4: 35, eq_mid_high: 35,
    eq_knob_5: 36, eq_high: 36, eq_knob_6: 37, eq_level: 37,
    eq_knob_7: 38, eq_knob_8: 39, eq_knob_9: 40, eq_knob_10: 41, eq_knob_11: 42, eq_knob_12: 43,

    nr_knob_1: 44, nr_knob_2: 45, nr_knob_3: 46, nr_knob_4: 47,

    mod_knob_1: 48, mod_knob_2: 49, mod_knob_3: 50, mod_knob_4: 51, mod_knob_5: 52, mod_knob_6: 53,

    dly_knob_1: 54, delay_time: 54, dly_knob_2: 55, delay_feedback: 55,
    dly_knob_3: 56, delay_mix: 56, dly_knob_4: 57, dly_knob_5: 58,
    dly_knob_6: 59, dly_knob_7: 60, dly_knob_8: 61,

    rvb_knob_1: 62, reverb_decay: 62, rvb_knob_2: 63, reverb_mix: 63,
    rvb_knob_3: 64, reverb_tone: 64, rvb_knob_4: 65,

    cab_knob_1: 66, cab_mic: 66, cab_knob_2: 67, cab_position: 67,
    cab_knob_3: 68, cab_distance: 68, cab_knob_4: 69, cab_level: 69,
    cab_knob_5: 70, cab_knob_6: 71,

    send: 72, return: 73, patch_min: 74, patch_max: 75, patch_level: 76,
    current_block: 77, pedal: 78, scene: 79, drum_enable: 80, drum_type: 81,
    drum_level: 82, loop_level: 83, loop_state: 84,
};

// Expose available keys
export const AVAILABLE_KEYS = Object.keys(MIDI_CC_MAP);
