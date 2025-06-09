from app.core import security
from app.db.models import User
from app.schemas.schemas import UserCreate
from app.cruds.user_crud import create_user
from sqlalchemy.orm import Session

def test_password_hashing():
    """
    Test that a password is correctly hashed and can be verified.
    """
    password = "a_strong_password"
    hashed_password = security.get_password_hash(password)
    
    # Assert that the hash is not the same as the original password
    assert password != hashed_password
    # Assert that the verification function works correctly
    assert security.verify_password(password, hashed_password)
    # Assert that verification fails with a wrong password
    assert not security.verify_password("wrong_password", hashed_password)


def test_jwt_token_creation_and_decoding(db_session: Session):
    """
    Test the full JWT lifecycle:
    1. Create a user.
    2. Create an access token for that user.
    3. Decode the token and verify the user.
    """
    # 1. Create a user in the test database
    user_schema = UserCreate(
        email="tokenuser@test.com", 
        username="tokenuser", 
        password="password123"
    )
    create_user(db=db_session, user=user_schema)

    # 2. Create an access token
    access_token = security.create_access_token(data={"sub": "tokenuser"})
    assert isinstance(access_token, str)

    # 3. Use the get_user_from_token helper to decode the token and fetch the user
    decoded_user = security.get_user_from_token(db=db_session, token=access_token)
    
    # 4. Assert that the correct user was retrieved
    assert decoded_user is not None
    assert isinstance(decoded_user, User)
    assert decoded_user.username == "tokenuser"


def test_get_user_from_invalid_token(db_session: Session):
    """
    Test that providing a bad token returns None.
    """
    invalid_token = "this.is.not.a.valid.token"
    user = security.get_user_from_token(db=db_session, token=invalid_token)
    assert user is None