TEST_PLAYER_TG_ID = 123456
TEST_PLAYER_VALID_USERNAME = "test_player"
TEST_PLAYER_INVALID_USERNAMES: list[str] = [
    "few",  # less than 5 characters
    "thequickbrownfoxjumpsoverthelazydog",  # more than 32 characters
    "no space",  # contains spaces
    "special!char",  # contains special characters
]
