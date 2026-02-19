def must_verified_email(user) -> bool:
    return user.is_active and user.email and user.email_verified

def must_verified_phone_number(user) -> bool:
    return user.is_active and user.phone_number and user.phone_number_verified