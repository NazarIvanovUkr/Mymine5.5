#mapnager
import pickle

class Mapmanager():
   """ Управління карткою """
   def __init__(self):
       self.model = 'block' # модель кубика лежить у файлі block.egg
       self.texture = 'block.png'
       self.colors = [
           (0.2, 0.2, 0.35, 1),
           (0.2, 0.5, 0.2, 1),
           (0.7, 0.2, 0.2, 1),
           (0.5, 0.3, 0.0, 1)
       ]
       self.startNew()

   def startNew(self):
       self.land = render.attachNewNode("Land")

   def getColor(self, z):
       if z < len(self.colors):
           return self.colors[z]
       else:
           return self.colors[len(self.colors) - 1]

   def addBlock(self, position):
       self.block = loader.loadModel(self.model)
       self.block.setTexture(loader.loadTexture(self.texture))
       self.block.setPos(position)
       self.color = self.getColor(int(position[2]))
       self.block.setColor(self.color)
       self.block.setTag("at", str(position))
       self.block.reparentTo(self.land)

   def clear(self):
       self.land.removeNode()
       self.startNew()

   def loadLand(self, filename):
       """створює карту землі з текстового файлу, повертає її розміри"""
       self.clear()
       y = 0
       with open(filename) as file:
           for line in file:
               x = 0
               line = line.split(' ')
               for z in line:
                   for z0 in range(int(z)+1):
                       self.addBlock((x, y, z0))
                   x += 1
               y += 1
       # сохраняем размеры карты
       self.size_x = x
       self.size_y = y
       return x, y

   def findBlocks(self, pos):
       return self.land.findAllMatches("=at=" + str(pos))

   def isEmpty(self, pos):
       blocks = self.findBlocks(pos)
       if blocks:
           return False
       else:
           return True

   def findHighestEmpty(self, pos):
        x,y,z = pos
        z = 1
        while not self.isEmpty((x,y,z)):
            z += 1
        return (x,y,z)

   def buildBlock(self, pos):
       x, y, z = pos
       new = self.findHighestEmpty(pos)
       if new[2] <= z + 1:
           self.addBlock(new)

   def delBlock(self, pos):
       blocks = self.findBlocks(pos)
       for block in blocks:
           block.removeNode()

   def saveMap(self):
       blocks = self.land.getChildren()
       with open("saved_map.dat", "wb") as saved_map:
           pickle.dump(len(blocks), saved_map)
           for block in blocks:
               x,y,z = block.getPos()
               pos = (int(x), int(y), int(z))
               pickle.dump(pos, saved_map)
       print("Map Saved")

   def loadMap(self):
       self.clear()
       try:
           with open("saved_map.dat", "rb") as sm:
               length = pickle.load(sm)
               for i in range(length):
                   pos = pickle.load(sm)
                   self.addBlock(pos)
           print("Map Loaded")
       except:
           print("Error map load")

   # === НОВОЕ ===
   def in_bounds(self, pos):
       """Проверка: внутри ли мира (для мобов и героя)"""
       x, y, z = pos
       return 0 <= x < self.size_x and 0 <= y < self.size_y

