from enum import StrEnum

class RoleEnum(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    TRAINER = "trainer"
    MEMBER = "member"
    GUEST = "guest"
    
    
    @classmethod
    def to_list(cls) -> list[str]:
        """Return a list of all role values."""
        return [role.value for role in cls]
    
    @classmethod
    def admin_roles(cls) -> list[str]:
        """Return a list of roles that have admin privileges."""
        return [cls.OWNER.value, cls.ADMIN.value]
    
    @classmethod
    def trainer_roles(cls) -> list[str]:
        """Return a list of roles that have trainer privileges."""
        return [cls.OWNER.value, cls.ADMIN.value, cls.TRAINER.value]
    
    @classmethod
    def regular_roles(cls) -> list[str]:
        """Return a list of regular user roles (non-admin, non-trainer)."""
        return [cls.MEMBER.value, cls.GUEST.value]
    
