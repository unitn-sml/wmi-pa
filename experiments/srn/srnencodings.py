

ENC_DEF = "def"
ENC_OR = "or"
ENC_XOR = "xor"
ENC_ALT = "alt"
ENC_NL = "nl" # do not label intervals with aux vars
ENCODINGS = [ENC_DEF, ENC_OR, ENC_XOR, ENC_ALT, ENC_NL]

AUX_IFF = 0
UNION_CONSTRAINTS = 1    
AUX_CONSTRAINTS = 2
THEORY_CHAINS = 3    
LABEL_AUX = 4    

def encoding_dict(enc_string):
    if enc_string  in [ENC_XOR, ENC_ALT, ENC_NL]:
        ac = 'xor'
    elif enc_string == ENC_OR :
        ac = 'or'
    else:
        ac = None

    return {AUX_IFF : enc_string not in [ENC_ALT, LABEL_AUX],
            UNION_CONSTRAINTS : not (enc_string == ENC_ALT),
            AUX_CONSTRAINTS : ac,
            THEORY_CHAINS : enc_string not in [ENC_ALT, ENC_DEF],
            LABEL_AUX: not (enc_string == ENC_NL)}
