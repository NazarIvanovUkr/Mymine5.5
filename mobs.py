# mobs.py
from panda3d.core import Vec3, Point3, CollisionNode, CollisionBox
import random, math


def aabb_overlap(center_a, half_a, center_b, half_b):
    """Проверка пересечения AABB хитбоксов в мировых координатах."""
    if abs(center_a.x - center_b.x) > (half_a.x + half_b.x):
        return False
    if abs(center_a.y - center_b.y) > (half_a.y + half_b.y):
        return False
    if abs(center_a.z - center_b.z) > (half_a.z + half_b.z):
        return False
    return True


class BaseMob:
    def __init__(self, pos, land, hp, speed, hero=None, color=(1, 1, 1, 1)):
        self.land = land
        self.hp = hp
        self.speed = speed
        self.hero = hero

        # модель
        self.hero_model = loader.loadModel("smiley")
        self.hero_model.setScale(0.3)
        self.hero_model.setPos(pos)
        self.hero_model.setColor(*color)
        self.hero_model.reparentTo(render)

        # хитбокс
        self.hitbox_center_local = Point3(0, 0, 0.8)
        self.hitbox_half_local = Vec3(0.6, 0.6, 1.2)

        cNode = CollisionNode('mob_hitbox')
        cBox = CollisionBox(self.hitbox_center_local,
                            self.hitbox_half_local.x,
                            self.hitbox_half_local.y,
                            self.hitbox_half_local.z)
        cNode.addSolid(cBox)
        self.hitbox = self.hero_model.attachNewNode(cNode)
        self.hitbox.show()

        # центр хитбокса
        self._hb_center_np = self.hero_model.attachNewNode("hb_center")
        self._hb_center_np.setPos(self.hitbox_center_local)

        # физика
        self.vz = 0.0
        self.gravity = -10.0
        self.jump_speed = 5.0
        self.on_ground = False

        # направление
        self.direction = Vec3(0, 0, 0)

    def update(self, dt):
        if self.hero_model.isEmpty():
            return
        self.move(dt)
        self.apply_gravity(dt)
        if self.hp <= 0:
            self.die()

    def move(self, dt):
        move = self.direction * self.speed * dt
        new_pos = self.hero_model.getPos() + move

        if not (0 <= new_pos.x < self.land.size_x and 0 <= new_pos.y < self.land.size_y):
            return

        front_block = (round(new_pos.x), round(new_pos.y), round(self.hero_model.getZ()))
        block_above = (front_block[0], front_block[1], front_block[2] + 1)

        if self.land.isEmpty(front_block):
            self.hero_model.setX(new_pos.x)
            self.hero_model.setY(new_pos.y)
        elif self.on_ground and self.land.isEmpty(block_above):
            self.vz = self.jump_speed
            self.on_ground = False

        if self.direction.length() > 1e-4:
            angle = math.degrees(math.atan2(self.direction.x, self.direction.y))
            self.hero_model.setH(angle)

    def apply_gravity(self, dt):
        # смерть в пустоте
        if self.hero_model.getZ() < -5:
            print("☠ Моб упал в пустоту!")
            self.die()
            return

        # гравитация (как было)
        self.vz += self.gravity * dt
        new_z = self.hero_model.getZ() + self.vz * dt

        foot_x = round(self.hero_model.getX())
        foot_y = round(self.hero_model.getY())
        foot_z = round(new_z - 0.5)

        if not self.land.isEmpty((foot_x, foot_y, foot_z)):
            self.hero_model.setZ(foot_z + 1)
            self.vz = 0
            self.on_ground = True
        else:
            self.hero_model.setZ(new_z)
            self.on_ground = False

    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.die()

    def die(self):
        if not self.hero_model.isEmpty():
            print("☠ Моб погиб")
            self.hero_model.removeNode()


class NeutralMob(BaseMob):
    """Нейтральный моб — гуляет случайно."""
    def __init__(self, pos, land, hp, speed, hero=None):
        super().__init__(pos, land, hp, speed, hero, color=(0.7, 0.9, 1.0, 1.0))
        self.wander_interval = 2.0
        self.time_since_last_turn = 0.0

    def update(self, dt):
        self.time_since_last_turn += dt
        if self.time_since_last_turn > self.wander_interval:
            angle = random.uniform(0, 360)
            rad = math.radians(angle)
            self.direction = Vec3(math.cos(rad), math.sin(rad), 0)
            self.time_since_last_turn = 0.0
        super().update(dt)


class AggressiveMob(BaseMob):
    """Агрессивный моб — идёт к герою и атакует при касании."""
    def __init__(self, pos, land, hp, speed, hero=None):
        super().__init__(pos, land, hp, speed, hero, color=(1.0, 0.4, 0.4, 1.0))
        self.attack_cooldown = 1.5
        self.time_since_attack = 0.0

    def update(self, dt):
        self.time_since_attack += dt

        if self.hero and not self.hero.hero.isEmpty() and self.hero.alive:
            hero_pos = self.hero.hero.getPos()
            mob_pos = self.hero_model.getPos()
            vec = hero_pos - mob_pos
            vec.z = 0
            if vec.length() > 0.1:
                vec.normalize()
                self.direction = vec

            self.try_attack()

        super().update(dt)

    def try_attack(self):
        if self.time_since_attack < self.attack_cooldown:
            return

        mob_center = self._hb_center_np.getPos(render)
        hero_center = self.hero._hb_center_np.getPos(render)

        mob_scale = self.hero_model.getScale().x
        mob_half = Vec3(self.hitbox_half_local.x * mob_scale,
                        self.hitbox_half_local.y * mob_scale,
                        self.hitbox_half_local.z * mob_scale)

        hero_scale = self.hero.hero.getScale().x
        hero_half = Vec3(self.hero.hitbox_half_local.x * hero_scale,
                         self.hero.hitbox_half_local.y * hero_scale,
                         self.hero.hitbox_half_local.z * hero_scale)

        if aabb_overlap(mob_center, mob_half, hero_center, hero_half):
            print("💢 Агрессивный моб ударил героя!")
            self.hero.take_damage(10)
            self.time_since_attack = 0.0
