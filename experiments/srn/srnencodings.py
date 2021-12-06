

ENC_DEF = "def"
ENC_OR = "or"
ENC_XOR = "xor"
ENC_ALT = "alt"
ENCODINGS = [ENC_DEF, ENC_OR, ENC_XOR, ENC_ALT]

AUX_IFF = 0
UNION_CONSTRAINTS = 1    
AUX_CONSTRAINTS = 2
THEORY_CHAINS = 3    

def encoding_dict(enc_string):
    if enc_string  in [ENC_XOR, ENC_ALT]:
        ac = 'xor'
    elif enc_string == ENC_OR :
        ac = 'or'
    else:
        ac = None

    return {AUX_IFF : not (enc_string == ENC_ALT),
            UNION_CONSTRAINTS : not (enc_string == ENC_ALT),
            AUX_CONSTRAINTS : ac,
            THEORY_CHAINS : enc_string not in [ENC_ALT, ENC_DEF]}
