#hero.py
from panda3d.core import WindowProperties, Vec3, CollisionNode, CollisionBox, Point3
from direct.showbase.InputStateGlobal import inputState
from direct.gui.DirectGui import DirectWaitBar, OnscreenText

# --- КЛАВИШИ ---
KEY_FORWARD = 'w'
KEY_BACK = 's'
KEY_LEFT = 'a'
KEY_RIGHT = 'd'
KEY_SWITCH_CAMERA = 'c'
KEY_DOWN = 'shift'
KEY_BUILD = "mouse3"
KEY_DESTROY = 'mouse1'
KEY_SAVE = "k"
KEY_LOAD = "l"
KEY_JUMP = "space"
KEY_ATTACK = "f"
KEY_TOGGLE_HITBOX = "f3"
KEY_RESPAWN = "r"   # новая клавиша возрождения


def aabb_overlap_world(center_a, half_a, center_b, half_b):
    """Проверка пересечения двух AABB в мировых координатах."""
    if (center_a.x + half_a.x < center_b.x - half_b.x) or (center_b.x + half_b.x < center_a.x - half_a.x):
        return False
    if (center_a.y + half_a.y < center_b.y - half_b.y) or (center_b.y + half_b.y < center_a.y - half_a.y):
        return False
    if (center_a.z + half_a.z < center_b.z - half_b.z) or (center_b.z + half_b.z < center_a.z - half_a.z):
        return False
    return True


class Hero:
    def __init__(self, pos, land):
        self.land = land

        # === модель игрока ===
        self.hero = loader.loadModel('smiley')
        self.hero.setColor(1, 0.5, 0)
        self.hero.setScale(0.3)
        self.hero.setPos(pos)
        self.hero.reparentTo(render)

        # хитбокс
        self.hitbox_center_local = Point3(0, 0, 1)
        self.hitbox_half_local = Vec3(0.6, 0.6, 1.5)

        cNode = CollisionNode('hero_hitbox')
        cBox = CollisionBox(self.hitbox_center_local,
                            self.hitbox_half_local.x,
                            self.hitbox_half_local.y,
                            self.hitbox_half_local.z)
        cNode.addSolid(cBox)
        self.hitbox = self.hero.attachNewNode(cNode)
        self.hitbox.show()

        # центр хитбокса в мировых координатах
        self._hb_center_np = self.hero.attachNewNode("hb_center")
        self._hb_center_np.setPos(self.hitbox_center_local)

        # здоровье
        self.max_hp = 100
        self.hp = self.max_hp

        self.hp_bar = DirectWaitBar(text="", value=self.hp,
                                    range=self.max_hp,
                                    pos=(0, 0, -0.95),
                                    scale=0.5,
                                    barColor=(1, 0, 0, 1))
        self.hp_text = OnscreenText(text=f"HP: {self.hp}/{self.max_hp}",
                                    pos=(0, -0.87),
                                    fg=(1, 1, 1, 1),
                                    scale=0.07,
                                    mayChange=True)

        # камера и управление
        self.cameraBind()
        self.accept_events()

        # параметры
        self.speed = 7
        self.sensitivity = 0.13
        self.vz = 0
        self.gravity = -10
        self.jump_speed = 5
        self.on_ground = False
        self.show_hitboxes = True

        # флаг жизни
        self.alive = True

        self.centerMouse()

        taskMgr.add(self.update_camera, "update_camera")
        taskMgr.add(self.update_movement, "update_movement")

    # ---------- ЗДОРОВЬЕ ----------
    def take_damage(self, amount):
        if not self.alive:
            return
        self.hp -= amount
        if self.hp < 0:
            self.hp = 0
        self.update_hp_bar()
        print(f"❤️ HP игрока: {self.hp}/{self.max_hp}")
        if self.hp <= 0:
            self.die()

    def heal(self, amount):
        if not self.alive:
            return
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        self.update_hp_bar()

    def update_hp_bar(self):
        self.hp_bar['value'] = self.hp
        self.hp_text.setText(f"HP: {self.hp}/{self.max_hp}")

    def die(self):
        print("☠ Игрок погиб!")
        self.hero.hide()
        self.hp = 0  # обязательно сбрасываем здоровье
        self.update_hp_bar()
        self.hp_text.setText("YOU DIED")
        self.alive = False

    def respawn(self):
        print(f"[DEBUG] попытка респавна, hp={self.hp}, alive={self.alive}")
        if self.hp > 0:
            return
        spawn_pos = (self.land.size_x // 2, self.land.size_y // 2, 4)
        self.hero.setPos(spawn_pos)
        self.hp = self.max_hp
        self.update_hp_bar()
        self.hero.show()
        self.hp_text.setText(f"HP: {self.hp}/{self.max_hp}")
        self.alive = True
        print("🔄 Игрок возродился!")

    # ---------- КАМЕРА ----------
    def cameraBind(self):
        base.disableMouse()
        base.camera.setH(180)
        base.camera.reparentTo(self.hero)
        base.camera.setPos(0, 0, 2)
        self.cameraOn = True

    def changeView(self):
        if self.cameraOn:
            base.camera.reparentTo(render)
            base.enableMouse()
            wp = WindowProperties()
            wp.setCursorHidden(False)
            base.win.requestProperties(wp)
            self.cameraOn = False
        else:
            self.cameraBind()

    def update_camera(self, task):
        if self.cameraOn and base.mouseWatcherNode.hasMouse() and self.alive:
            md = base.win.getPointer(0)
            x, y = md.getX(), md.getY()
            cx = base.win.getXSize() // 2
            cy = base.win.getYSize() // 2
            dx = (x - cx) * self.sensitivity
            dy = (y - cy) * self.sensitivity
            self.hero.setH(self.hero.getH() - dx)
            new_pitch = max(-60, min(60, base.camera.getP() - dy))
            base.camera.setP(new_pitch)
            self.centerMouse()
        return task.cont

    def centerMouse(self):
        wp = WindowProperties()
        wp.setCursorHidden(True)
        base.win.requestProperties(wp)
        cx = base.win.getXSize() // 2
        cy = base.win.getYSize() // 2
        base.win.movePointer(0, cx, cy)

    def update_movement(self, task):
        if not self.alive:
            return task.cont
        dt = globalClock.getDt()
        direction = Vec3(0, 0, 0)

        # --- движение по WASD (у тебя уже есть) ---
        if inputState.isSet(KEY_FORWARD):
            direction.y -= 1
        if inputState.isSet(KEY_BACK):
            direction.y += 1
        if inputState.isSet(KEY_LEFT):
            direction.x += 1
        if inputState.isSet(KEY_RIGHT):
            direction.x -= 1

        if direction.length() > 0:
            direction.normalize()
            world_move = render.getRelativeVector(self.hero, direction) * self.speed * dt
            new_pos = self.hero.getPos() + world_move
            if 0 <= new_pos.x < self.land.size_x and 0 <= new_pos.y < self.land.size_y:
                target_block = (round(new_pos.x), round(new_pos.y), round(self.hero.getZ()))
                if self.land.isEmpty(target_block):
                    self.hero.setPos(new_pos)

        # --- гравитация (оставь как у тебя было!) ---
        self.vz += self.gravity * dt
        new_z = self.hero.getZ() + self.vz * dt
        foot_x, foot_y, foot_z = round(self.hero.getX()), round(self.hero.getY()), round(new_z - 0.5)
        if not self.land.isEmpty((foot_x, foot_y, foot_z)):
            self.hero.setZ(foot_z + 1)
            self.vz, self.on_ground = 0, True
        else:
            self.hero.setZ(new_z)
            self.on_ground = False

        # === смерть в пустоте ===
        if self.hero.getZ() < -5:
            print("☠ Игрок упал в пустоту!")
            self.die()
            return task.cont

        return task.cont

    def jump(self):
        if not self.alive:
            return
        if self.on_ground:
            self.vz = self.jump_speed
            self.on_ground = False

    # ---------- АТАКА ----------
    def attack(self):
        if not self.alive:
            print("[DEBUG] Герой мёртв, атака невозможна")
            return
        if not hasattr(base, "mobs_list"):
            print("[DEBUG] mobs_list не существует")
            return

        print("[DEBUG] Герой атакует, найдено мобов:", len(base.mobs_list))

        hero_center_world = self._hb_center_np.getPos(render)
        hero_scale = self.hero.getScale().x
        hero_half_world = Vec3(self.hitbox_half_local.x * hero_scale,
                               self.hitbox_half_local.y * hero_scale,
                               self.hitbox_half_local.z * hero_scale)

        for mob in list(base.mobs_list):
            if mob.hero_model.isEmpty():
                continue
            mob_center_world = mob._hb_center_np.getPos(render)
            mob_scale = mob.hero_model.getScale().x
            mob_half_world = Vec3(mob.hitbox_half_local.x * mob_scale,
                                  mob.hitbox_half_local.y * mob_scale,
                                  mob.hitbox_half_local.z * mob_scale)

            if aabb_overlap_world(hero_center_world, hero_half_world, mob_center_world, mob_half_world):
                mob.take_damage(20)
                print("Моб получил урон!")

    # ---------- ХИТБОКСЫ ----------
    def toggle_hitboxes(self):
        if not self.alive:
            return
        self.show_hitboxes = not self.show_hitboxes
        if self.show_hitboxes:
            self.hitbox.show()
        else:
            self.hitbox.hide()
        if hasattr(base, "mobs_list"):
            for mob in base.mobs_list:
                if mob.hero_model.isEmpty():
                    continue
                if self.show_hitboxes:
                    mob.hitbox.show()
                else:
                    mob.hitbox.hide()


    # ---------- СТРОИТЕЛЬСТВО ----------
    def build(self):
        if not self.alive:
            return
        pos = (round(self.hero.getX()), round(self.hero.getY()), round(self.hero.getZ()))
        self.land.addBlock(pos)

    def destroy(self):
        if not self.alive:
            return
        if not base.mouseWatcherNode.hasMouse():
            return
        dir_vec = base.camera.getQuat(render).getForward()
        dir_vec.normalize()
        start_pos = self.hero.getPos()
        for dist in range(1, 5):
            tx = round(start_pos.x + dir_vec.x * dist)
            ty = round(start_pos.y + dir_vec.y * dist)
            tz = round(start_pos.z + dir_vec.z * dist)
            target_block = (tx, ty, tz)
            if not self.land.isEmpty(target_block):
                self.land.delBlock(target_block)
                print(f"🪓 Герой сломал блок: {target_block}")
                break

    # ---------- СОБЫТИЯ ----------
    def accept_events(self):
        inputState.watchWithModifiers(KEY_FORWARD, KEY_FORWARD)
        inputState.watchWithModifiers(KEY_BACK, KEY_BACK)
        inputState.watchWithModifiers(KEY_LEFT, KEY_LEFT)
        inputState.watchWithModifiers(KEY_RIGHT, KEY_RIGHT)
        inputState.watchWithModifiers(KEY_DOWN, KEY_DOWN)

        base.accept(KEY_SWITCH_CAMERA, self.changeView)
        base.accept(KEY_BUILD, self.build)
        base.accept(KEY_DESTROY, self.destroy)   # ЛКМ ломаем блок
        base.accept(KEY_SAVE, self.land.saveMap)
        base.accept(KEY_LOAD, self.land.loadMap)
        base.accept(KEY_JUMP, self.jump)
        base.accept(KEY_ATTACK, self.attack)
        base.accept(KEY_TOGGLE_HITBOX, self.toggle_hitboxes)
        base.accept(KEY_RESPAWN, self.respawn)  # R = респавн


