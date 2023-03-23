import re
import time
from random import randint, choice


class BoardException(Exception):
    pass


class BoardOutException(BoardException):
    def __str__(self):
        return "За пределами поля!"


class BoardBusyException(BoardException):
    def __str__(self):
        return "Клетка занята!"


class BoardShipFailureException(BoardException):
    pass


class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"Dot({self.x}, {self.y})"


class Ship:
    def __init__(self, start, horizontal, length):
        self.start = start
        self.horizontal = horizontal
        self.length = length
        self.lives = length

    @property
    def dots(self):
        ship_dots = []
        for i in range(self.length):
            cur_x = self.start.x
            cur_y = self.start.y
            if self.horizontal:
                cur_y += i
            else:
                cur_x += i
            ship_dots.append(Dot(cur_x, cur_y))
        return ship_dots

    def is_hit(self, shot):
        return shot in self.dots


class Board:
    def __init__(self, size=6, is_hidden=False):
        self.size = size
        self.field = [["O"] * size for _ in range(size)]
        self.busy = []
        self.ships = []
        self.count = 0
        self.is_hidden = is_hidden

    def __str__(self):
        res = "    " + "".join([f' {i} |' for i in range(1, self.size + 1)])
        for i, row in enumerate(self.field):
            res += f"\n {i + 1} | " + " | ".join(row) + " |"
        res += "\n"
        if self.is_hidden:
            res = res.replace("■", "O")
        return res

    def is_out(self, dot):
        return not ((0 <= dot.x < self.size) and (0 <= dot.y < self.size))

    def add_ship(self, ship):
        for d in ship.dots:
            if self.is_out(d) or d in self.busy:
                raise BoardShipFailureException()
        for d in ship.dots:
            self.field[d.x][d.y] = "■"
            self.busy.append(d)
        self.contour(ship)
        self.ships.append(ship)

    def contour(self, ship, is_visible=False):
        (x, y) = (ship.start.x, ship.start.y) if ship.horizontal else (ship.start.y, ship.start.x)
        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + ship.length + 1):
                cur = Dot(i, j) if ship.horizontal else Dot(j, i)
                if self.is_out(cur) or cur in self.busy:
                    continue
                if is_visible:
                    self.field[cur.x][cur.y] = "."
                self.busy.append(cur)

    def shot(self, d):
        if self.is_out(d):
            raise BoardOutException()
        if d in self.busy:
            raise BoardBusyException()
        self.busy.append(d)

        for ship in self.ships:
            if ship.is_hit(d):
                self.field[d.x][d.y] = "X"
                ship.lives -= 1
                if ship.lives > 0:
                    print("Ранен!")
                    return True
                else:
                    print("Убит!")
                    self.count += 1
                    self.contour(ship, True)
                    return False
        self.field[d.x][d.y] = "."
        print("Мимо!")
        return False

    def begin(self):
        self.busy = []


class Player:
    def __init__(self, board, enemy, prev=None):
        if prev is None:
            prev = []
        self.board = board
        self.enemy = enemy
        self.prev = []

    def ask(self):
        raise NotImplementedError()

    def move(self):
        is_sunk = self.enemy.count
        while True:
            try:
                target = self.ask()
                repeat = self.enemy.shot(target)
                if repeat:
                    self.prev.append(target)
                if is_sunk != self.enemy.count:
                    self.prev = []
                return repeat
            except BoardException as e:
                print(e)


class AI(Player):
    def __init__(self, board, enemy):
        super().__init__(board, enemy)

    def ask(self):
        time.sleep(1)
        d = choice(self.ai_brain(self.enemy))               #выбирает ход случайно из набора, предложенного ai_brain
        print(f"Ход компьютера: {d.x + 1} {d.y + 1}")
        return d

    # если раненых кораблей врага нет, пробивает диагонали как предложено тут https://habr.com/ru/post/180995/
    # если есть одно попадание и корабль не убит - пробивает четыре соседние клетки
    # если есть 2 попадания - пробивает клетки "по краям" подбитого корабля
    # добивает корабль пока не утопит, после - возвращается к диагоналям
    def ai_brain(self, enemy):
        shot_set = []
        if len(self.prev) == 2:
            if self.prev[0].x == self.prev[1].x:
                shot_set = [Dot(self.prev[0].x, min(self.prev[0].y, self.prev[1].y) - 1),
                            Dot(self.prev[0].x, max(self.prev[0].y, self.prev[1].y) + 1)]
            else:
                shot_set = [Dot(min(self.prev[0].x, self.prev[1].x) - 1, self.prev[0].y),
                            Dot(max(self.prev[0].x, self.prev[1].x) + 1, self.prev[0].y)]
            shot_set = [x for x in shot_set if x not in enemy.busy]
        elif len(self.prev) == 1:
            shot_set = [Dot(self.prev[0].x + 1, self.prev[0].y),
                        Dot(self.prev[0].x - 1, self.prev[0].y),
                        Dot(self.prev[0].x, self.prev[0].y + 1),
                        Dot(self.prev[0].x, self.prev[0].y - 1)]
            shot_set = [x for x in shot_set if x not in enemy.busy]
        else:
            shot_set = [Dot(i, i) for i in range(0, 6)]
            shot_set.extend([Dot(i, i + 3) for i in range(0, 3)])
            shot_set.extend([Dot(i + 3, i) for i in range(0, 3)])
            shot_set = [x for x in shot_set if x not in enemy.busy]
            if not shot_set:
                shot_set = [Dot(i, i - 1) for i in range(1, 6)]
                shot_set.extend([Dot(i, i + 2) for i in range(0, 4)])
                shot_set.extend([Dot(0, 5), Dot(5, 0)])
                shot_set = [x for x in shot_set if x not in enemy.busy]
                if not shot_set:
                    shot_set = [Dot(i, j) for i in range(0, 6) for j in range(0, 6)]
                    shot_set = [x for x in shot_set if x not in enemy.busy]
        return shot_set


class User(Player):
    def ask(self):
        while True:
            cors = input("Введите две координаты через пробел: ")
            if not re.match(r'^\d+\s\d+$', cors):
                print("Введите два числа!")
                continue
            x, y = map(int, cors.split())
            return Dot(x - 1, y - 1)


class Game:
    def __init__(self, size=6):
        self.size = size
        player_1 = self.random_board()
        player_2 = self.random_board()
        self.user = User(player_1, player_2)
        # self.user = AI(player_1, player_2)          # включить для проверки AI против AI
        self.ai = AI(player_2, player_1)
        player_2.is_hidden = True
        self.player_1 = player_1

    def try_board(self):
        lens = [3, 2, 2, 1, 1, 1, 1]
        board = Board(size=self.size)
        for l in lens:
            for attempt in range(0, 2000):
                ship = Ship(Dot(randint(0, self.size - 1), randint(0, self.size - 1)), randint(0, 1), l)
                try:
                    board.add_ship(ship)
                    break
                except BoardShipFailureException:
                    pass
                if attempt == 1999:
                    return None
        board.begin()
        return board

    def random_board(self):
        board = None
        while board is None:
            board = self.try_board()
        return board

    def greet(self):
        print("                      ", "-" * 20)
        print('               Приветсвуем вас в игре "Морской бой"!')
        print("                      ", "-" * 20)
        print("                        формат ввода: x y ")
        print("                        x - номер строки  ")
        print("                        y - номер столбца ")

    def loop(self):
        num = 0
        while True:
            print("                      ", "-" * 20)
            print("     Доска пользователя:                    Доска компьютера:")
            for a in zip(str(self.user.board).split("\n"), str(self.ai.board).split("\n")):
                print(f'{a[0]}          {a[1]}')
            if num % 2 == 0:
                print("Ход пользователя")
                repeat = self.user.move()
            else:
                print("Ход компьютера...")
                repeat = self.ai.move()
            if repeat:
                num -= 1
            if self.user.board.count == 7:
                print("Компьютер победил!")
                break
            if self.ai.board.count == 7:
                print("Пользователь победил!")
                break
            num += 1

    def start(self):
        self.greet()
        self.loop()


g = Game(6)
g.start()
