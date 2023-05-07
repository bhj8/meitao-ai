class ErrorCode:
    INVALID_CREDENTIALS = 1001
    USER_ALREADY_EXISTS = 1002
    EMAIL_NOT_VALID = 1003
    PASSWORD_NOT_VALID = 1004
    ACCOUNT_NOT_ACTIVE = 1005
    ACCOUNT_LOCKED = 1006
    TOKEN_EXPIRED = 1007
    TOKEN_INVALID = 1008
    RESOURCE_NOT_FOUND = 1009
    PERMISSION_DENIED = 1010
    OPERATION_FAILED = 1011
    DATA_INTEGRITY_VIOLATION = 1012
    BAD_REQUEST = 1013
    FORBIDDEN = 1014
    TOO_MANY_REQUESTS = 1015
    INTERNAL_SERVER_ERROR = 1016
    SERVICE_UNAVAILABLE = 1017
    INVALID_INPUT = 1018
    IP_ALREADY_REGISTERED =1019
    #不是会员，无权使用
    NOT_MEMBER = 1020
    VERIFICATION_CODE_INCORRECT=1021    
    
    # ... 其他错误码


class ErrorMessage:
    INVALID_CREDENTIALS = "Invalid credentials"
    USER_ALREADY_EXISTS = "Username already exists"
    EMAIL_NOT_VALID = "Email is not valid"
    PASSWORD_NOT_VALID = "Password is not valid"
    ACCOUNT_NOT_ACTIVE = "Account is not active"
    ACCOUNT_LOCKED = "Account is locked"
    TOKEN_EXPIRED = "Token has expired"
    TOKEN_INVALID = "Token is invalid"
    RESOURCE_NOT_FOUND = "Resource not found"
    PERMISSION_DENIED = "Permission denied"
    OPERATION_FAILED = "Operation failed"
    DATA_INTEGRITY_VIOLATION = "Data integrity violation"
    BAD_REQUEST = "Bad request"
    FORBIDDEN = "Forbidden"
    TOO_MANY_REQUESTS = "Too many requests"
    INTERNAL_SERVER_ERROR = "Internal server error"
    SERVICE_UNAVAILABLE = "Service unavailable"
    INVALID_INPUT = "Invalid input"
    IP_ALREADY_REGISTERED = "IP already registered"
    NOT_MEMBER="您没有订阅会员，无权使用。请订阅后再试"
    # ... 其他错误消息
    VERIFICATION_CODE_INCORRECT="验证码错误"
