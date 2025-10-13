from django.core.signing import TimestampSigner, SignatureExpired, BadSignature

TOKEN_MAX_AGE = 60 * 60  # 1 hour


def create_token(user_id):
    #Create signed token
    signer = TimestampSigner()
    return signer.sign(str(user_id))


def validate_token(token):
    #Check if token is valid and not expired
    if not token:
        return False

    try:
        signer = TimestampSigner()
        signer.unsign(token, max_age=TOKEN_MAX_AGE) 
        return True
    except (SignatureExpired, BadSignature): #return false if token has expired or is invalid
        return False
