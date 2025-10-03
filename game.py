#game.py
from direct.showbase.ShowBase import ShowBase
from mapmanager import Mapmanager
from hero import Hero
from mobs import NeutralMob, AggressiveMob
import random


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # создаём карту
        self.land = Mapmanager()
        x, y = self.land.loadLand("land.txt")
        self.land.size_x = x
        self.land.size_y = y

        # создаём героя
        self.hero = Hero((x // 2, y // 2, 4), self.land)

        base.camLens.setFov(90)

        # Параметры времени и мобов
        self.time_of_day = 0.0  # секунды
        self.mob_spawn_timer = 0.0
        self.mobs = []
        self.max_mobs = 30

        # Задача на обновление мира каждый кадр
        taskMgr.add(self.update_world, "update_world")

    def update_world(self, task):
        dt = globalClock.getDt()

        # Обновление времени суток
        self.time_of_day += dt
        self.time_of_day %= 1200  # цикл 20 минут (1200 сек)

        # Проверка дня/ночи
        is_day = self.time_of_day < 600

        # Таймер спавна
        self.mob_spawn_timer += dt
        if self.mob_spawn_timer >= 5.0:  # каждые 5 секунд
            self.mob_spawn_timer = 0.0
            self.spawn_mobs(is_day)

        # Обновление мобов
        for mob in list(self.mobs):
            mob.update(dt)
            if mob.hero_model.isEmpty():
                self.mobs.remove(mob)

        return task.cont

    def spawn_mobs(self, is_day):
        if len(self.mobs) >= self.max_mobs:
            return  # слишком много мобов

        # Координаты героя
        hx, hy, hz = round(self.hero.hero.getX()), round(self.hero.hero.getY()), round(self.hero.hero.getZ())

        # Генерация точки рядом с героем
        spawn_x = hx + random.randint(-20, 20)
        spawn_y = hy + random.randint(-20, 20)
        spawn_z = hz

        # Проверка границ карты
        if not (0 <= spawn_x < self.land.size_x and 0 <= spawn_y < self.land.size_y):
            return

        pos = (spawn_x, spawn_y, spawn_z)

        # Выбор типа моба в зависимости от времени суток
        if is_day:
            mob = NeutralMob(pos, self.land, hp=30, speed=2, hero=self.hero)
        else:
            mob = AggressiveMob(pos, self.land, hp=50, speed=2.5, hero=self.hero)

        self.mobs.append(mob)


# Запуск игры
game = Game()
game.run()

