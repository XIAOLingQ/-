from user import User

def test_borrowbook():
    # 假设用户ID为 1
    user_id = 1003
    User.borrowbook(user_id)

def test_returnbook():
    # 假设用户ID为 1
    user_id = 1002
    User.returnbook(user_id)

def test_queryms():
    User.queryms()

def test_querymybook():
    # 假设用户ID为 1
    user_id = 1002
    User.querymybook(user_id)

if __name__ == "__main__":
    User.borrowbook(1002)
    User.returnbook(1002)

