import pygame
import random
import math

#window settings
screenWidth = 1400
screenHeight = 800
fps = 60
mainFontSize = 45
textFontSize = 15
smallFontSize = 10

#game setup 
# PLEASE REFER TO THE README TXT TO SEE THE TUTORIALS I USED TO HELP ME LEARN PYGAME AND HOW TO USE IT.
pygame.init()
window = pygame.display.set_mode((screenWidth,screenHeight))
timer = pygame.time.Clock()
pygame.display.set_caption("The Crucible")
timerCount = 0 #to create a count that goes up by 1 (refer to blit smallStartText)
timeLeft = 15                                   #For the game over screen
pygame.time.set_timer(pygame.USEREVENT, 1600) #For the game over screen
levels = [] # the various levels are appended below when we make the level class
currentLevelNum = 0 # we shall index through the list "levels" to determine which level we are on
levelIsClear = False #flag to check if current level is clear
inStartMenu = True  # we start at the start menu
inSelectionMenu = False # selection menu comes after the start menu
nonstopping = False # we assume standard mode first
addedOneAlready = False # if we are doing infinite mode, we must add one level

allSprites = pygame.sprite.Group()
mobs = pygame.sprite.Group()
platforms = pygame.sprite.Group()
flags = pygame.sprite.Group()

#variables
spawnX = 30
spawnY = 30
width = 40
height = 40
velY = 1
velX = 10
accelY = 1
jumpSpeed = -7
ezSpeed = 1
lengthOfLevel = 5800
groundLevel = screenHeight - 50
noiseCap = 10
playerStandardHealth = 100
dmgBoostDuration = 6000

# inspired from 15-112 notes on basic I/O (Strings notes)
def getHighScore(path):
    with open(path, "rt") as f:
        try:
            HS = int(f.read())
            return HS
        except:
            HS = 0   # if we cannot open file for some reason, high score is 0
            return HS
highScore = getHighScore("highscore.txt")

#colors
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)
yellow = (255, 255, 0)
skyBlue = (135, 206, 235)

#load images (sprites)
slashRight = pygame.image.load("items/slashRight.png").convert()
attackZero = pygame.image.load("items/ninja/attack_1.png").convert()
idleZero = pygame.image.load("items/ninja/idle_0x.png").convert()
jumpZero = pygame.image.load("items/ninja/jump_0.png").convert()

bat = pygame.image.load("items/batidle.png").convert_alpha()
sleepingAlpha = pygame.image.load("items/alphaWolfSleep.png").convert()
alphaWolfIdle = pygame.image.load("items/alphaWolfIdle.png").convert()
alphaWolfHowl = pygame.image.load("items/alphaWolfHowl.png").convert()
commonWolfIdle = pygame.image.load("items/timberWolfIdle.png").convert()
healerWolfIdle = pygame.image.load("items/healerWolfIdle.png").convert()
finishFlag = pygame.image.load("items/flag.png").convert_alpha()
rockImage = pygame.image.load("items/rock.png").convert()

healthPickup = pygame.image.load("items/PowerUp/health.png").convert()
attackPickupImg = pygame.image.load("items/PowerUp/attackBoost.png").convert()

selectionMenuBG = pygame.image.load("items/menuBackground.png").convert()

#load fonts
mainFont = pygame.font.Font("items/Fipps.otf", mainFontSize)
textFont = pygame.font.Font("items/Fipps.otf", textFontSize)
smallFont = pygame.font.Font("items/Fipps.otf", smallFontSize)

#Establish some start menu text(boxes) and pause menu text
bigStartText = mainFont.render("The Crucible", True, black)
smallStartText = textFont.render("Press G to start!", True, black)
pausedText = mainFont.render("Paused", True, black)
smallPausedText = textFont.render("Press P to unpause!", True, black)
levelClearText = textFont.render("Press N to move on to next level!", True, black)
shopOptionText = textFont.render("Press B to go to Shop!", True, black)
stageClearText = mainFont.render("Level Clear!", True, black)
batAdviceText = textFont.render("Rats! Got killed by Bats! Try to analyze how they drop their rocks!", True, red)
wolfAdviceText = textFont.render("Did you cry wolf? Try to analyze their jumping pattern...", True, red)
healerAdviceText = textFont.render("Healers are extremely weak without their alphas! Try to isolate them!", True, red)
alphaAdviceText = textFont.render("These big alphas start asleep. Try staying QUIET next time?", True, red)
fellAdviceText = textFont.render("Maybe try turning around next time? The abyss reaches quite far down.", True, red)

#oop platforms (solid terrain)
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        pygame.sprite.Sprite.__init__(self)  #for pygame run the init of the sprite
        self.image = pygame.Surface((width, height))
        self.image.fill(red)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mask = pygame.mask.from_surface(self.image) #convert_alpha()

#oop player (the player controlled character)
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)  #for pygame run the init of the sprite
        self.movingLeft = False
        self.movingRight = False
        self.image = idleZero
        self.image.set_colorkey(white)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.velX = 0
        self.velY = 0
        self.mask = pygame.mask.from_surface(self.image) #convert_alpha()
        self.health = playerStandardHealth
        self.gauge = pygame.Surface((self.health, 30))
        self.gauge.fill(red)
        self.gameOver = False
        self.damageable = True
        self.immune = False
        self.numOfJumps = 0
        self.jumping = False
        self.noise = 0  # noise level is initially 0
        self.noiseStatus = "Quiet"
        self.noiseColor = green
        self.attackReload = pygame.USEREVENT + 1
        self.canAttack = True
        self.fellToDeath = False # for the dying screen message
        self.score = 0  # score is initially 0
        self.overheal = False   # initially no overheal (100 hp)
        self.damageBoosted = False  # not damage boosted initially
        self.damageBoostDuration = pygame.USEREVENT + 6 # duration of damage boost
        self.startDmgBoostTimer = None
        self.damageBoostColor = green   # initially green (because always starts at max duration)

    def noisiness(self):
        if (self.noise >= 8):
            self.noiseStatus = "LOUD"
            self.noiseColor = red
        elif (self.noise < 8 and self.noise >= 4):
            self.noiseStatus = "Noisy"
            self.noiseColor = yellow
        else:
            self.noiseStatus = "Quiet"
            self.noiseColor = green

    def attack(self):
        if (self.canAttack):
            self.image = attackZero
            self.image.set_colorkey(white)
            pygame.time.set_timer(self.attackReload, 800)
            slash = Slash()
            currentLevel.allSprites.add(slash)
            self.canAttack = False # on reload
            self.noise += 0.5 # attacking makes noise

    def jump(self):
        self.jumping = True
        self.velY = jumpSpeed #and gravity will proceed to pull this character down (because no longer colliding)
        self.image = jumpZero #in a jump right now (so change animation)
        self.image.set_colorkey(white)
        if (self.noise < noiseCap):
            self.noise += 2     # jumping adds to noise
    
    def moveX(self, dx):        # need to check one axis at a time (check x axis movement first)
        self.rect.x += dx
        if (self.noise < noiseCap):      # noise limit is 10
            self.noise += abs(dx/30)    # the amount of noise generated by player corresponds to how much they travel (before stopping)
        hitP = pygame.sprite.spritecollide(player, currentLevel.platforms, False)
        for platform in hitP:
            if (dx > 0): # moving right
                self.rect.right = platform.rect.left
            if (dx < 0): # moving left
                self.rect.left = platform.rect.right
    
    def moveY(self, dy):        # now check y axis movement
        self.rect.y += dy
        hitP = pygame.sprite.spritecollide(player, currentLevel.platforms, False)
        for platform in hitP:
            if (dy > 0): # moving down
                self.rect.bottom = platform.rect.top
                self.image = idleZero  # now back to idle animation
                self.jumping = False
                self.numOfJumps = 0     # once the ground is touched reset the jump counter
                self.velY = 0   # on the ground
            if (dy < 0): # moving up
                self.rect.top = platform.rect.bottom
                self.velY = 0   # hit a object above

    def update(self):
        if (inStartMenu == False):
        #smooth movement
            keys = pygame.key.get_pressed()
            if keys[ pygame.K_RIGHT ]:
                self.velX = velX
                self.movingLeft = False
                self.movingRight = True
                self.moveX(self.velX)
            elif keys[ pygame.K_LEFT ]:
                self.velX = -1*velX
                self.movingLeft = True
                self.movingRight = False
                self.moveX(self.velX)
            #health bar
            if (self.health > playerStandardHealth + 10): # player health cannot exceed the absolute max health
                self.health = playerStandardHealth + 10
            if (self.overheal == False and self.health > playerStandardHealth):    # if player is not in overheal status cap is at maxHealth
                self.health = playerStandardHealth
            if (self.health < playerStandardHealth):
                self.overheal = False
            if (self.health >= 0):
                self.barImage = pygame.Surface((self.health, 30))
                self.barImage.fill(green)
            if (self.health <= 0):
                self.health = 0
                self.gameOver = True
            #gravity
            self.moveY(self.velY)
            #if not moving, noise level decreases, but cannot go below 0
            if (self.velX == 0 and self.noise > 0):
                self.noise -= 0.03
            self.noisiness()  # always check for noise level
            # character falls out of the world
            if (isWithinScreen(self) == False): 
                self.fellToDeath = True
                self.health = 0
            # going left or going right (sprite facing direction)
            if (self.movingLeft == True):
                self.image = pygame.transform.flip(idleZero, True, False)
                if (self.jumping == True):
                    self.image = pygame.transform.flip(jumpZero, True, False)
            elif (self.movingRight == True):
                self.image = idleZero
                if (self.jumping == True):
                    self.image = jumpZero

# generate a new slash everytime the player attacks
class Slash(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.kill()     # need to get rid of "slash" animation when not swinging
        self.damage = 30    # the "standard" slash
        if (player.damageBoosted == True):  # if the damageBoosted is on, every slash we perform has +10 damage
            self.damage += 10
        self.slashDuration = pygame.USEREVENT + 3
        pygame.time.set_timer(self.slashDuration, 400)
    
    #change depending on which direction facing (when not moving left or right default slash is right)
    def update(self):
        if (player.movingRight == True or (player.movingRight == False and player.movingLeft == False)):
            self.image = slashRight
            self.rect = self.image.get_rect()
            self.image = pygame.transform.scale(self.image, (self.rect.width*5, self.rect.height*5))
            self.image.set_colorkey(black)
            self.rect = self.image.get_rect()
            self.mask = pygame.mask.from_surface(self.image)
            self.rect.x = player.rect.x + player.rect.width  # next to the player (NEED TO CHANGE DIRECTION)
            self.rect.y = player.rect.y + (player.rect.height/10) # next to player
        elif (player.movingLeft == True):
            self.image = pygame.transform.flip(slashRight, True, False)
            self.rect = self.image.get_rect()
            self.image = pygame.transform.scale(self.image, (self.rect.width*5, self.rect.height*5))
            self.image.set_colorkey(black)
            self.rect = self.image.get_rect()
            self.mask = pygame.mask.from_surface(self.image)
            self.rect.x = player.rect.x - player.rect.width  # next to the player (NEED TO CHANGE DIRECTION)
            self.rect.y = player.rect.y + (player.rect.height/10) # next to player
        # add the damage to mobs
        attackedMobs = pygame.sprite.spritecollide(self, currentLevel.mobs, False)
        if (attackedMobs):    # if there is a collision (because it is a list when there is one)
            for mob in attackedMobs:
                if (mob.damageable):
                    mob.health -= self.damage   # deals damage (as of now, 30 damage)
                    mob.damageable = False
                    mob.timeDamaged = pygame.time.get_ticks()
                    mob.immuneTime = 800
                elif (mob.damageable == False):
                    now = pygame.time.get_ticks()
                    if (now - mob.timeDamaged >= mob.immuneTime):
                        mob.damageable = True

class Pickup(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = healthPickup
        self.image.set_colorkey(white)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mask = pygame.mask.from_surface(self.image)
        self.velY = 0
        
    def moveY(self, dy):
        self.rect.y += dy
        pickupHitP = pygame.sprite.spritecollide(self, currentLevel.platforms, False)
        for platform in pickupHitP:
            if (dy > 0): # moving down
                self.rect.bottom = platform.rect.top
                self.velY = 0   # on the ground

    def update(self):
        # pickups also have gravity
        self.moveY(self.velY)
        artificialGravity(self)
    
    def effect(self):   # this "parent" class has been defined as a standard health pickup, so heal
        if (player.health < 100): # can only perform effect if player health is less than max
            player.health += 15
            self.kill() # pickup goes away
        elif (player.health == 100):    # only when hp is at max of 100 can you overheal (even at 99 cannot overheal)
            player.health += 10
            player.overheal = True  # player is "overhealed"
            self.kill()

class attackPickup(Pickup):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = attackPickupImg
        self.image.set_colorkey(white)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mask = pygame.mask.from_surface(self.image)
        self.velY = 0

    def effect(self):   # overridden from parent class
        pygame.time.set_timer(player.damageBoostDuration, dmgBoostDuration)
        player.startDmgBoostTimer = pygame.time.get_ticks()
        player.damageBoosted = True
        self.kill()

class Rock(pygame.sprite.Sprite):
    def __init__(self, batToAttach):
        pygame.sprite.Sprite.__init__(self)
        self.image = rockImage
        self.image.set_colorkey(white)
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.batAttach = batToAttach
        self.rect.midtop = self.batAttach.rect.midbottom
        self.letGo = False
        self.velY = 0
        self.damage = 0
        self.canDrop = False

    def moveY(self, dy):        # now check y axis movement
        self.rect.y += dy
        self.damage += self.velY//11 # while falling, gather damage
        rockHitP = pygame.sprite.spritecollide(self, currentLevel.platforms, False)
        for platform in rockHitP:
            if (dy > 0): # moving down
                self.rect.bottom = platform.rect.top
                self.velY = 0   # on the ground
                self.damage = 0 # on the ground it does no damage

    def update(self):
        self.dropOrNotRect = pygame.Rect((self.rect.bottomleft), (self.rect.width, groundLevel-self.rect.bottom-20))
        if (self.letGo == False):
            self.rect.midtop = self.batAttach.rect.midbottom
            if (self.batAttach.health <= 0):
                self.kill()     # player should work to kill the bats before they drop rocks
        if (self.letGo == True and self.canDrop == True):   # if we can drop the rocks (no platform above player)
            self.moveY(self.velY)
            artificialGravity(self)
        
class Mob(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)  #for pygame run the init of the sprite
        self.image = bat
        self.rect = self.image.get_rect()
        self.rect.x = x     # spawn location x coord
        self.rect.y = y     # spawn location y coord
        self.kill()     #implement a kill so that they can die (when called to die)
        self.poofState = False  #all mobs are poof-able
        self.health = 0     # health (will be set with each individual mob)
        self.velY = 0
        self.damageable = True 
        self.timeDamaged = None # to keep track of when damaged, resistance calc
        self.immuneTime = player.attackReload # cannot take damage until the sword can swing again
        self.scoreWorth = 0 # how much the mob is "worth" for killing them
    
    def moveX(self, dx):        # need to check one axis at a time (check x axis movement first)
        self.rect.x += dx
        mobHitP = pygame.sprite.groupcollide(currentLevel.mobs, currentLevel.platforms, False, False)
        for key in mobHitP:
            for value in mobHitP[key]:
                if (dx > 0): # moving right
                    key.rect.right = value.rect.left
                if (dx < 0): # moving left
                    key.rect.left = value.rect.right
    
    def moveY(self, dy):        # now check y axis movement
        self.rect.y += dy
        mobHitP = pygame.sprite.groupcollide(currentLevel.mobs, currentLevel.platforms, False, False)
        for key in mobHitP:
            for value in mobHitP[key]:
                if (dy > 0): # moving down
                    key.rect.bottom = value.rect.top
                    key.velY = 0   # on the ground
                if (dy < 0): # moving up
                    key.rect.top = value.rect.bottom
                    key.velY = 0   # hit a object above

    def poof(self):     # the poof characteristic (only poof-ed at the end of each level)
        player.immune = True
        self.poofText = textFont.render("*POOF*", True, black)
        self.image = self.poofText
        window.blit(self.poofText, (self.rect.x, self.rect.y))
        self.poofState = True

    def update(self):
        if (self.poofState):
            self.image = self.poofText
        # mobs also have gravity (except for bats, but we can override that)
        self.moveY(self.velY)
        # character falls out of the world
        if (isWithinScreen(self) == False): 
            self.health = 0

class Bat(Mob):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = bat
        self.rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image, (self.rect.width*2, self.rect.height*2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mask = pygame.mask.from_surface(self.image)
        self.health = 30
        self.healthMax = 30
        self.damage = 5
        self.damageMax = 8
        self.holdingRock = True
        self.rock = Rock(self)
        self.scoreWorth = 70

    def dropRock(self):
        self.rock.letGo = True
    
    def update(self):
        if (self.poofState == False):
            targetX = player.rect.x
            targetY = player.rect.y
            if (self.holdingRock == True):
                if (self.rect.x < targetX):
                    self.moveX(ezSpeed)
                if (self.rect.x > targetX):
                    self.moveX(-ezSpeed)
                if (self.rect.x == player.rect.x): # make sure that there isn't a platform above the player before dropping
                    if (self.rock.canDrop):
                        self.dropRock()
                        self.holdingRock = False
            elif (self.holdingRock == False):
                if (self.rect.x < targetX):
                    self.moveX(ezSpeed)
                if (self.rect.x > targetX):
                    self.moveX(-ezSpeed)
                if (self.rect.y < targetY):
                    self.moveY(ezSpeed)
                if (self.rect.y > targetY):
                    self.moveY(-ezSpeed) 
            if (self.health <= 0):   # no more health so ded
                player.score += self.scoreWorth # bats award 70 points as of now
                self.kill()
            # character falls out of the world
            if (isWithinScreen(self) == False): 
                self.health = 0

class Wolf(Mob):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = commonWolfIdle
        self.image.set_colorkey(white)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mask = pygame.mask.from_surface(self.image)
        self.health = 40
        self.healthMax = 40
        self.damage = 8
        self.damageMax = 11
        self.checkAboveRect = pygame.Rect(self.rect.x, 0, self.rect.width, self.rect.y)
        self.canJump = True
        self.jumpReloadComplete = True
        self.jumpReload = pygame.USEREVENT + 4
        self.scoreWorth = 50

    def jump(self):
        self.velY = jumpSpeed #and gravity will proceed to pull this character down (because no longer colliding)
        self.jumpReloadComplete = False
        pygame.time.set_timer(self.jumpReload, random.randint(2500, 3500))

    def update(self):
        self.checkAboveRect = pygame.Rect(self.rect.x, 0, self.rect.width, self.rect.y)
        if (self.health <= 0):   # no more health so ded
            player.score += self.scoreWorth # wolves award 50 points as of now
            self.kill()
        if (self.poofState == False):
            targetX = player.rect.x
            targetY = player.rect.y
            if (self.rect.y > player.rect.y):   # the wolf is below the player 
                if (self.canJump == True and self.jumpReloadComplete == True):
                    self.jump()
            if (self.rect.x < targetX):
                self.moveX(ezSpeed)
            elif (self.rect.x > targetX):
                self.moveX(-ezSpeed)
            #gravity
            self.moveY(self.velY)
            # character falls out of the world
            if (isWithinScreen(self) == False): 
                self.health = 0
   

class alphaWolf(Wolf):
    def __init__(self, x, y):
        Wolf.__init__(self, x, y)
        self.image = alphaWolfIdle
        self.image.set_colorkey(white)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mask = pygame.mask.from_surface(self.image) 
        self.health = 80
        self.awake = False      # these alpha wolves start asleep
        self.howlReload = pygame.USEREVENT + 2
        self.howling = False
        self.canHowl = True
        self.damage = 10
        self.damageMax = 13
        self.scoreWorth = 120

    def sleep(self):
        if (self.awake == False):
            self.image = sleepingAlpha
            self.image.set_colorkey(white)

    def howl(self):
        self.image = alphaWolfHowl
        self.image.set_colorkey(white)
        guardWolf1 = Wolf(player.rect.x + 200, player.rect.y - 30)
        guardWolf2 = Wolf(player.rect.x - 200, player.rect.y - 30)
        currentLevel.mobs.add(guardWolf1)
        currentLevel.mobs.add(guardWolf2)
        currentLevel.allSprites.add(guardWolf1)
        currentLevel.allSprites.add(guardWolf2)
        self.canHowl = False   # goes on cool down

    def awakeBehavior(self):
        # behavior when awake (i.e. howl to summon 2 common wolves 
        # every 13 seconds and stay behind other wolves)
        self.image = alphaWolfIdle
        self.image.set_colorkey(white)
        smallestDist = 100000 # an absurdly large value that will never be possible in the game
        mobToPlayerX = 0
        for mob in currentLevel.mobs:
            if (isinstance(mob, Wolf) and type(mob) != alphaWolf): # if the mob is a wolf type, the alpha needs to retreat "behind" another wolf
                mobToPlayerX = mob.rect.x - player.rect.x  # (ensure there is always another wolf has distance closer to player)
                mobToPlayerY = mob.rect.y - player.rect.y  # (AND that there is a wolf BETWEEN the player and alpha if on same side of player)
                mobDistanceToPlayer = math.sqrt(mobToPlayerX**2 + mobToPlayerY**2)  # distance formula
                if (mobDistanceToPlayer < smallestDist):
                    smallestDist = mobDistanceToPlayer
        alphaToPlayerX = self.rect.x - player.rect.x
        alphaToPlayerY = self.rect.y - player.rect.y
        alphaDistanceToPlayer = math.sqrt(alphaToPlayerX**2 + alphaToPlayerY**2)
        if (alphaDistanceToPlayer < smallestDist and mobToPlayerX != 0):  # while the alpha is closer to the player than another wolf
            if (alphaToPlayerX > 0 and mobToPlayerX > 0): # both the small and alpha wolf are to the right of the player
                self.moveX(ezSpeed)
            elif (alphaToPlayerX < 0 and mobToPlayerX < 0): # both the small and alpha wolf are to the left of the player
                self.moveX(-ezSpeed)
            elif (alphaToPlayerX > 0 and mobToPlayerX < 0): # alpha wolf is to the right of the player, small wolf to the left
                self.moveX(ezSpeed)
            elif (alphaToPlayerX < 0 and mobToPlayerX > 0): # alpha wolf is to the left of the player, small wolf to the right
                self.moveX(-ezSpeed)

    def update(self):  # overridden from parent mob class
        # insert code for awaking here
        # include awakeBehavior in here
        if (self.health <= 0):   # no more health so ded
            player.score += self.scoreWorth # alphas award 120 points as of now
            self.kill()
        #gravity
        self.moveY(self.velY)
        # character falls out of the world
        if (isWithinScreen(self) == False): 
            self.health = 0
        #starts off sleeping
        self.sleep()
        if (self.poofState):
            self.image = self.poofText
        elif (player.noise > 8 or self.awake == True):
            if (mobIsWithinScreen(self)):  # can only perform its behavior when the wolf is on the screen
                self.awake = True  # if the player makes too much noise, they awake
                if (self.canHowl): # needs to also be fully visible on screen
                    self.howl()
                    pygame.time.set_timer(self.howlReload, 13000)  # can use this ability every 13 seconds
                self.awakeBehavior()

class healerWolf(Wolf):
    def __init__(self, x, y):
        Wolf.__init__(self, x, y)
        self.image = healerWolfIdle
        self.image.set_colorkey(white)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mask = pygame.mask.from_surface(self.image) 
        self.health = 60
        self.healthMax = 60
        self.healerHowlReload = pygame.USEREVENT + 5
        self.canHowl = True
        self.howling = False
        self.healingAmount = 5
        self.damageBuff = 3
        self.damage = 8
        self.damageMax = 11
        self.teleportMax = 2
        self.teleportNum = 0
        self.jumpNum = 0
        self.jumpMax = 1
        self.scoreWorth = 100

    def howl(self):
        if (mobIsWithinScreen(self) and self.canHowl):  # can only perform its behavior when the wolf is on the screen
            screenWolves = []
            for mob in currentLevel.mobs:
                if (isinstance(mob, Wolf) and mobIsWithinScreen(mob)):
                    screenWolves.append(mob)
            if (len(screenWolves) >= 3):
                for wolf in screenWolves:
                    if (wolf.health < wolf.healthMax):
                        wolf.health += self.healingAmount   # heal the wounded wolves around
                    if (wolf.damage < wolf.damageMax):
                        wolf.damage += self.damageBuff    # increase the attacks of other wolves
            self.canHowl = False # cooldown

    def alertBehavior(self):
        healerToPlayerX = self.rect.x - player.rect.x
        healerToPlayerY = self.rect.y - player.rect.y
        healerDistanceToPlayer = math.sqrt(healerToPlayerX**2 + healerToPlayerY**2)
        if (healerDistanceToPlayer < 200):
            if (self.teleportNum < self.teleportMax):
                #teleport to the nearest Alpha
                for mob in currentLevel.mobs:
                    if (isinstance(mob, alphaWolf)):
                        self.rect.x = mob.rect.x + 100
                        self.rect.y = mob.rect.y
                        self.teleportNum += 1
            else:
                if (player.movingLeft == True):
                    self.moveX(-ezSpeed)
                    if (self.jumpNum < self.jumpMax):
                        self.jump()
                        self.jumpNum += 1
                elif (player.movingRight == True):
                    self.moveX(ezSpeed)
                    if (self.jumpNum < self.jumpMax):
                        self.jump()
                        self.jumpNum += 1
    
    def update(self):
        if (self.health <= 0):   # no more health so ded
            player.score += self.scoreWorth # healers award 100 points as of now
            self.kill()
        if (self.poofState == False):
            self.howl()
            pygame.time.set_timer(self.healerHowlReload, 5000) # the healer wolf can howl every 5 seconds
            self.alertBehavior()
            #gravity
            self.moveY(self.velY)
            # character falls out of the world
            if (isWithinScreen(self) == False): 
                self.health = 0

class Flag(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)  #for pygame run the init of the sprite
        self.image = finishFlag
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image.convert_alpha())
        self.rect.x = lengthOfLevel - 200           #will move to end of level soon (to determine where the finish should be)
        self.rect.y = 500
    
class Level():
    def __init__(self):
        self.allSprites = pygame.sprite.Group()
        self.flags = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.mobs = pygame.sprite.Group()
        self.rocks = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()
        self.background = pygame.image.load("items/mountain/background.png").convert()

    def update(self): 
        redrawDuringGame()
        drawGameOver(timeLeft)

    def spawnPlatforms(self):
        ground = Platform(0, groundLevel, lengthOfLevel, 100)
        walls = Platform(-100, groundLevel - 100, 100, 200)
        walls2 = Platform(lengthOfLevel, groundLevel - 100, 100, 200)
        self.platforms.add(ground)
        self.allSprites.add(ground)
        self.platforms.add(walls)
        self.allSprites.add(walls)
        self.platforms.add(walls2)
        self.allSprites.add(walls2)
        for interval in range(200, lengthOfLevel - 400, 500):
            length = random.randrange(100, 300)
            spawnHeight = random.randrange(550, groundLevel - 2*player.rect.height)
            newPlatform = Platform(interval, spawnHeight, length, 50)
            self.platforms.add(newPlatform)
            self.allSprites.add(newPlatform)

    # input in form of dictionary called spawnQuota --> {Bat: numBats, Wolf: numWolves, healerWolf: numHealerWolves, alphaWolf: numAlphaWolves}
    def spawnMobs(self, spawnQuota):
        for mobType in spawnQuota:
            for count in range(spawnQuota[mobType]):
                spawnXCoord = random.randrange(1300, lengthOfLevel - 400)
                spawnHeight = random.randrange(300, groundLevel - 2*player.rect.height)
                batSpawnHeight = random.randrange(200, groundLevel - 6*player.rect.height)
                if (mobType == "Bat"):
                    mobToBeAdded = Bat(spawnXCoord, batSpawnHeight)
                    batsRock = mobToBeAdded.rock
                    self.allSprites.add(batsRock)
                    self.rocks.add(batsRock)
                elif (mobType == "Wolf"):
                    mobToBeAdded = Wolf(spawnXCoord, spawnHeight)
                elif (mobType == "alphaWolf"):
                    mobToBeAdded = alphaWolf(spawnXCoord, spawnHeight)
                elif (mobType == "healerWolf"):
                    mobToBeAdded = healerWolf(spawnXCoord, spawnHeight)
                self.mobs.add(mobToBeAdded)
                self.allSprites.add(mobToBeAdded)
    
    def spawnPickups(self, difficulty):
        for interval in range(200, lengthOfLevel - 400, 450):
            spawnChance = random.randint(1,100)
            if (currentLevelNum <= 3):
                spawnCutoff = 30 - 5*difficulty
            else:
                spawnCutoff = 10 # spawn rate does not go below 10
            pickupChooser = random.randint(1,2)
            if (spawnChance <= spawnCutoff):  # spawnCutoff gets lower as levels go up (less chance of spawn and therefore harder)
                if (pickupChooser == 1):
                    pickupSpawn = Pickup(interval, random.randrange(300, groundLevel - 2*player.rect.height))
                    self.pickups.add(pickupSpawn)
                    self.allSprites.add(pickupSpawn)
                else:
                    pickupSpawn = attackPickup(interval, random.randrange(300, groundLevel - 2*player.rect.height))
                    self.pickups.add(pickupSpawn)
                    self.allSprites.add(pickupSpawn)

class tutorial(Level):
    def __init__(self):
        super().__init__()
        self.background = pygame.Surface((0, 0))
        self.allSprites.add(player) # the player must exist in each level
        player.rect.x = spawnX
        player.rect.y = spawnY
        self.spawnTutorialPlatforms()
    
    def spawnTutorialPlatforms(self):
        ground = ground = Platform(0, groundLevel, screenWidth, 100)
        walls = Platform(-100, groundLevel - 700, 100, 700)
        walls2 = Platform(screenWidth, groundLevel - 700, 100, 700)
        self.platforms.add(ground)
        self.allSprites.add(ground)
        self.platforms.add(walls)
        self.allSprites.add(walls)
        self.platforms.add(walls2)
        self.allSprites.add(walls2)

class normalLevel(Level):
    def __init__(self, spawnQuota, difficulty):
        super().__init__()
        self.allSprites.add(player) # the player must exist in each level
        flag = Flag()
        self.flags.add(flag)
        self.allSprites.add(flag)
        self.spawnPlatforms() 
        self.spawnMobs(spawnQuota)
        self.spawnPickups(difficulty) #testing

class endLevel(Level):
    def __init__(self):
        super().__init__()
        self.allSprites.add(player)
        self.spawnEndPlatforms()
    
    def spawnEndPlatforms(self):
        ground = ground = Platform(0, groundLevel, screenWidth, 100)
        walls = Platform(-100, groundLevel - 700, 100, 700)
        walls2 = Platform(screenWidth, groundLevel - 100, 100, 700)
        self.platforms.add(ground)
        self.allSprites.add(ground)
        self.platforms.add(walls)
        self.allSprites.add(walls)
        self.platforms.add(walls2)
        self.allSprites.add(walls2)

player = Player(spawnX, spawnY)

def standardMode():
#(THIS IS SETUP FOR THE "DEFAULT" MODE)
    levels.append(tutorial())
    spawnQuota = { "Bat":1, "Wolf":1, "healerWolf":1, "alphaWolf":2 }
    L1 = normalLevel(spawnQuota, 1)
    levels.append(L1)
    spawnQuota = { "Bat":2, "Wolf":4, "healerWolf":2, "alphaWolf":3 }
    L2 = normalLevel(spawnQuota, 2)
    levels.append(L2)
    spawnQuota = { "Bat":3, "Wolf":6, "healerWolf":3, "alphaWolf":5 }
    L3 = normalLevel(spawnQuota, 3)
    levels.append(L3)
    L4 = endLevel()
    levels.append(L4)
# SET UP FOR THE DEFAULT MODE ABOVE

def infiniteMode():
    levels.append(tutorial())

def generateEnemyCounts(difficultyLevel):
    difficultyMultiplier = 1.4
    enemySpawnCounts = [] 
    for i in range(4):  # because we have 4 enemy types
        enemyEstimate = round(difficultyMultiplier * difficultyLevel)
        if (i < 2): # this is the enhancing pattern for the easy 2 mobs (bat and wolf)
            enemyEstimate += random.randint(-2, 1) # spice things up a bit
        else:
            enemyEstimate += random.randint(-1, 0)
        enemySpawnCounts.append(enemyEstimate)
    return enemySpawnCounts

# various player statistics drawing
def updateStats():
    window.blit(player.gauge, (100, 5))
    window.blit(player.barImage, (100, 5))
    healthText = textFont.render(f"Health: {player.health}/100", True, black)
    if (player.overheal == True):   # if the player is overhealed right now
        overhealStatus = textFont.render(f"Overhealed!", True, black)
        window.blit(overhealStatus, (10, 30))
    if (player.damageBoosted == True):
        damageBoostStatus = textFont.render(f"Damage Boost!", True, player.damageBoostColor)
        window.blit(damageBoostStatus, (600, 30))
    noiseText = textFont.render("NOISE: ", True, black)
    noiseLevelText = textFont.render(f"{player.noiseStatus}", True, player.noiseColor)
    scoreText = textFont.render(f"SCORE: {player.score}", True, black)
    window.blit(scoreText, (600, 5))
    window.blit(healthText, (10, 5))
    window.blit(noiseText, (300, 5))
    window.blit(noiseLevelText, (400, 5))

#algorithm to center text position (default is bottom right corner position)
def adjustTextPos(txt, side):
    widthAdjust = txt.get_rect().width // 2
    heightAdjust = txt.get_rect().height // 2
    if (side == 'w'):
        return widthAdjust
    elif (side == 'h'):
        return heightAdjust

def artificialGravity(entity):
    currentTime = pygame.time.get_ticks()
    if (currentTime % 10 < 4):
        entity.velY += accelY 

def isWithinScreen(entity):
    #if (entity.rect.x >= 0 and entity.rect.x <= screenWidth - entity.rect.width):
    if (entity.rect.y < screenHeight):
        return True
    return False

def mobIsWithinScreen(entity):
    if (entity.rect.x > 0 - entity.rect.width and entity.rect.x < screenWidth):
        if (entity.rect.y > 0 - entity.rect.height and entity.rect.y < screenHeight):
            return True
    return False

def pause(notLevelClearPause):
    paused = True
    while (paused == True):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if (notLevelClearPause == True):     # if it is NOT A LEVEL CLEAR PAUSE, it's a "normal" pause
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    paused = False
                pauseTextX = screenWidth//2 - adjustTextPos(pausedText, 'w')
                pauseTextY = screenHeight//2 - adjustTextPos(pausedText, 'h')
                smallPauseTextX = screenWidth//2 - adjustTextPos(smallPausedText, 'w')
                smallPauseTextY = screenHeight//2 - adjustTextPos(smallPausedText, 'h')
                window.blit(pausedText, (pauseTextX, pauseTextY))
                window.blit(smallPausedText, (smallPauseTextX, smallPauseTextY + mainFontSize))
                if (nonstopping == True):
                    gamemodeStatus = f"INFINITE and you are on Level {currentLevelNum}"
                else:
                    gamemodeStatus = f"STANDARD and you are on Level {currentLevelNum}"
                pauseInfoText = textFont.render(f"You are currently playing the gamemode {gamemodeStatus}!", True, black)
                window.blit(pauseInfoText, (smallPauseTextX - 300, smallPauseTextY - 2*mainFontSize))
        pygame.display.update()

def tutorialProcedure():
    if (player.rect.x < 500):
        welcomeText = textFont.render(f"Welcome to The Crucible! The current High Score is {highScore}!", True, black)
        window.blit(welcomeText, (100, 100))
        skipText = textFont.render("Press S to skip this tutorial if you're confident!", True, black)
        window.blit(skipText, (100, 150))
        backText = mainFont.render("Press B to go back to selection", True, black)
        window.blit(backText, (100, 400))
        movementText = textFont.render("Use arrow keys to move right and see the rest of the tutorial!", True, black)
        window.blit(movementText, (100, 200))
        if (nonstopping == True):
            gameStatus = "INFINITE"
            gamemodeText = textFont.render(f"Infinite Gamemode! If you have a lot of time and want an 'endless' challenge", True, black)
        else:
            gameStatus = "STANDARD"
            gamemodeText = textFont.render("Three Levels! Get to the end, and you're the WORTHY", True, black)
        statusText = textFont.render(f"Currently playing {gameStatus} gamemode!", True, black)
        window.blit(statusText, (100, 300))
        window.blit(gamemodeText, (100, 360))
    elif (player.rect.x < 900 and player.rect.x > 500):
        movementText = textFont.render("Press X to attack      Press P to pause      Press Space to jump", True, black)
        window.blit(movementText, (100, 100))
        scoreExplanation = textFont.render("Beside your NOISE, you will find your SCORE! If high enough, it may be kept!", True, black)
        window.blit(scoreExplanation, (100, 150))
        jumpText = textFont.render("You can even double jump! Now keep going right for enemy descriptions!", True, black)
        window.blit(jumpText, (100, 200))
        window.blit(pygame.transform.scale(finishFlag, (128,128)), (50, 430))
        flagDescription = textFont.render("This is the Stage Clear Flag! Touch this to *POOF* all the enemies on the current level!", True, black)
        flag2Description = textFont.render("You can press N once you reach this to move on to the next level!", True, black)
        window.blit(flagDescription, (180, 430))
        window.blit(flag2Description, (180, 460))
        healthPickupDesc = textFont.render("Health Pickup! You get 15 more health! If you are at 100, you get OVERHEAL up to 110 health!", True, black)
        window.blit(healthPickupDesc, (180, 300))
        window.blit(healthPickup, (100, 300))
        attackPickupDesc = textFont.render("Attack Pickup! You temporarily gain +10 attack! See the meter that pops up for duration!", True, black)
        window.blit(attackPickupDesc, (180, 350))
        window.blit(attackPickupImg, (100, 350))
    elif (player.rect.x > 900):
        window.blit(pygame.transform.scale(bat, (66, 40)), (20, 100))
        batDescription = textFont.render("This smol boi is a bat, watch out! It'll try to drop rocks that increase in damage as they fall!", True, black)
        bat2Description = textFont.render("Try to kill bats while they are still holding their rocks!", True, black)
        window.blit(batDescription, (180, 100))
        window.blit(bat2Description, (180, 120))
        window.blit(commonWolfIdle, (20, 180))
        wolfDescription = textFont.render("This dude is a wolf, They'll follow you around and can also jump!", True, black)
        wolf2Description = textFont.render("Try to avoid them if you can!", True, black)
        window.blit(wolfDescription, (180, 180))
        window.blit(wolf2Description, (180, 200))
        window.blit(healerWolfIdle, (20, 260))
        healerDescription = textFont.render("This fella is a healer wolf, They can teleport to the nearest Alpha wolf if you get too close!", True, black)
        healer2Description = textFont.render("They can also provide healing and damage buffs to other wolves if > 3 wolves on the screen!", True, black)
        window.blit(healerDescription, (180, 260))
        window.blit(healer2Description, (180, 280))
        window.blit(alphaWolfIdle, (20, 340))
        alphaDescription = textFont.render("This bad boi is an alpha, They can spawn 2 wolves on your sides! And, they keep a wolf between", True, black)
        alpha2Description = textFont.render("you and themself. They DO start off asleep! Watch your NOISE in the top left!", True, black)
        window.blit(alphaDescription, (180, 340))
        window.blit(alpha2Description, (180, 360))
        goFightText = textFont.render("Now go prove your worth. See you on the other side! Press S to go!", True, black)
        window.blit(goFightText, (180, 600))

def endProcedure():
    celebrationMainText = mainFont.render("CONGRATULATIONS!", True, black)
    celebrationSubText = textFont.render("You've Done It!", True, black)
    exitTrollText = textFont.render("EXIT TO THE RIGHT, or is it?", True, black)
    actualExitText = textFont.render("Press R to return to Menu (Your score will be remain)", True, black)
    mainTextX = screenWidth//2 - adjustTextPos(bigStartText, 'w')
    mainTextY = screenHeight//2 - adjustTextPos(bigStartText, 'h')
    smallTextX = screenWidth//2 - adjustTextPos(smallStartText, 'w')
    smallTextY = screenHeight//2 - adjustTextPos(smallStartText, 'h')
    window.blit(celebrationMainText, (mainTextX, mainTextY))
    window.blit(celebrationSubText, (smallTextX, smallTextY + 2*mainFontSize))
    window.blit(exitTrollText, (smallTextX, smallTextY + 3*mainFontSize))
    window.blit(actualExitText, (smallTextX, smallTextY + 4*mainFontSize))

def redrawDuringGame():
    #Draw Graphics during actual gameplay
    window.fill(skyBlue)
    window.blit(currentLevel.background, (0,0))
    if (currentLevelNum == 0):  # we are in the tutorial
        tutorialProcedure()
    if (isinstance(currentLevel, endLevel)):
        endProcedure()
    currentLevel.allSprites.update() # create and update function for level superclass (THIS SHOULD BE NOT OVERRIDDEN AS SAME FOR ALL LEVELS)
    if (checkFinish):
        drawLevelClear(currentLevelNum)
    updateStats()
    currentLevel.allSprites.draw(window)
    pygame.display.update()

def redrawInStart():
    #Start Menu Text and draw the things at the start menu
    window.fill(white)
    mainTextX = screenWidth//2 - adjustTextPos(bigStartText, 'w')
    mainTextY = screenHeight//2 - adjustTextPos(bigStartText, 'h')
    smallTextX = screenWidth//2 - adjustTextPos(smallStartText, 'w')
    smallTextY = screenHeight//2 - adjustTextPos(smallStartText, 'h')
    window.blit(bigStartText, (mainTextX, mainTextY))
    if (timerCount % 10 < 5):   #half the time show the small text
        window.blit(smallStartText, (smallTextX, smallTextY + mainFontSize)) #to offset right below main text

def redrawInSelection(buttonXCoord, blueButtonYCoord, greenButtonYCoord, buttonWidth, buttonHeight):
    window.fill(white)
    window.blit(selectionMenuBG, (0, 50))
    selectionMenuHeader = mainFont.render("Select your Game Mode", True, black)
    window.blit(selectionMenuHeader, (100, 50))
    pygame.draw.rect(window, skyBlue, (buttonXCoord, blueButtonYCoord, buttonWidth, buttonHeight))
    pygame.draw.rect(window, green, (buttonXCoord, greenButtonYCoord, buttonWidth, buttonHeight))
    infiniteModeText = textFont.render("  Infinite Mode", True, black)
    window.blit(infiniteModeText, (buttonXCoord, screenHeight//2-75))
    standardModeText = textFont.render(" Standard Mode", True, black)
    window.blit(standardModeText, (buttonXCoord, screenHeight//2+95))

def drawGameOver(timeLeft):
    while (player.gameOver == True):
        window.fill(black)
        bigEndText = mainFont.render("You Died!", True, red)
        mainTextX = screenWidth//2 - adjustTextPos(bigEndText, 'w')
        mainTextY = screenHeight//2 - adjustTextPos(bigEndText, 'h')
        window.blit(bigEndText, (mainTextX, mainTextY))
        smallEndText = textFont.render(f"Terminating in {timeLeft}", True, red)
        smallTextX = screenWidth//2 - adjustTextPos(smallEndText, 'w')
        smallTextY = screenHeight//2 - adjustTextPos(smallEndText, 'h')
        window.blit(smallEndText, (smallTextX, smallTextY + mainFontSize))

        if (player.fellToDeath == True):
            window.blit(fellAdviceText, (300, smallTextY + 2*mainFontSize))
        elif (type(lastAttackedMob) == Bat):
            window.blit(batAdviceText, (300, smallTextY + 2*mainFontSize))
        elif (type(lastAttackedMob) == Wolf):
            window.blit(wolfAdviceText, (300, smallTextY + 2*mainFontSize))
        elif (type(lastAttackedMob) == healerWolf):
            window.blit(healerAdviceText, (300, smallTextY + 2*mainFontSize))
        elif (type(lastAttackedMob) == alphaWolf):
            window.blit(alphaAdviceText, (300, smallTextY + 2*mainFontSize))
        if (player.score > highScore):
            newHSText = textFont.render(f"NEW HIGH SCORE!", True, green)
            window.blit(newHSText, (smallTextX, smallTextY - 6*mainFontSize))
            modifyHighScore("highscore.txt")
        else:
            highScoreText = textFont.render(f"High Score: {highScore}", True, green)
            window.blit(highScoreText, (smallTextX, smallTextY - 5*mainFontSize))
        keptScoreText = textFont.render(f"Score: {player.score}", True, red)
        window.blit(keptScoreText, (smallTextX, smallTextY - 4*mainFontSize))
        
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            #keep track of the time when game over
            if event.type == pygame.USEREVENT:
                timeLeft -= 1
                if (timeLeft == 0):
                    pygame.quit()
                    quit()
            #if event.type == pygame.KEYDOWN and event.key == pygame.K_r:

def drawLevelClear(currentLevelNum):
    levelClearTextX = screenWidth//2 - adjustTextPos(levelClearText, 'w')
    levelClearTextY = screenHeight//2 - adjustTextPos(levelClearText, 'h')
    window.blit(stageClearText, (levelClearTextX, levelClearTextY - 2*mainFontSize))
    window.blit(levelClearText, (levelClearTextX, levelClearTextY))

def modifyHighScore(path):
    with open(path, "wt") as f:
        f.write(str(player.score))

#Game loop
run = True
while run:
    if (inStartMenu == True):
        timerCount += 1         #add to timer counter
        timer.tick(5)           #5 is a slower (at most 5 frames per second) for the start menu (so we can create blipping effects)
        redrawInStart()

    #Check for inputs in game
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        if (inSelectionMenu == True):
            mousePosition = pygame.mouse.get_pos()
            clicked = pygame.mouse.get_pressed()
            buttonXCoord = screenWidth//3
            blueButtonYCoord = screenHeight//2-100
            greenButtonYCoord = screenHeight//2+70
            buttonWidth = 200
            buttonHeight = 100
            redrawInSelection(buttonXCoord, blueButtonYCoord, greenButtonYCoord, buttonWidth, buttonHeight)
            if (mousePosition[0] > buttonXCoord and mousePosition[0] < buttonXCoord + buttonWidth):
                if (mousePosition[1] < blueButtonYCoord + buttonHeight and mousePosition[1] > blueButtonYCoord):
                    infiniteDescription = textFont.render(f"  Infinite Gamemode! If you have a lot of time", True, black)
                    infinite2Description = textFont.render(f"  and desire an 'endlessly' increasing challenge", True, black)
                    window.blit(infiniteDescription, (buttonXCoord + buttonWidth, blueButtonYCoord))
                    window.blit(infinite2Description, (buttonXCoord + buttonWidth, blueButtonYCoord+25))
                    if (clicked[0] == 1):
                        print("INFINITE MODE")
                        levels = [] # need to clear levels or else there might be something wack when we switch gamemodes
                        infiniteMode()
                        currentLevel = levels[currentLevelNum]
                        nonstopping = True
                        inSelectionMenu = False
                elif (mousePosition[1] < greenButtonYCoord + buttonHeight and mousePosition[1] > greenButtonYCoord):
                    standardDescription = textFont.render(f"  Standard Gamemode! If you want to be the hero", True, black)
                    standard2Description = textFont.render(f"  and see if you are up to the task of 3 Levels!", True, black)
                    window.blit(standardDescription, (buttonXCoord + buttonWidth, greenButtonYCoord))
                    window.blit(standard2Description, (buttonXCoord + buttonWidth, greenButtonYCoord+25))
                    if (clicked[0] == 1):
                        print("STANDARD MODE")
                        levels = [] # need to clear levels or else there might be something wack when we switch gamemodes
                        standardMode()
                        nonstopping = False
                        currentLevel = levels[currentLevelNum]
                        inSelectionMenu = False # because we are taken to the tutorial (as of now its the standard version)

        if (levelIsClear == True):
            player.immune = True    # player is immune because the level is clear
            if event.type == pygame.KEYDOWN and event.key == pygame.K_n:
                #move on to the next level
                currentLevelNum += 1
                currentLevel = levels[currentLevelNum]
                addedOneAlready = False # (for the infinite mode) now that we in new level, we haven't added the next one yet
                levelIsClear = False
                player.immune = False   # once the "levelIsClear" is false, the player is no longer immune
        if (inStartMenu == True and event.type == pygame.KEYDOWN and event.key == pygame.K_g):
            inStartMenu = False
            inSelectionMenu = True
        if (inStartMenu == False and inSelectionMenu == False): # ALL OF THIS CODE IS WHILE IN ACTUAL GAMEPLAY (NOT START/SELECTION MENU)
            if (currentLevelNum == 0):  # if we are on the tutorial
                if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                    # CONSIDER THE INFINITE MODE
                    if (nonstopping == True):
                        spawnQuota = { "Bat":1, "Wolf":3, "healerWolf":1, "alphaWolf":1 } # will change soon
                        levelToBeAdded = normalLevel(spawnQuota, currentLevelNum + 1) # infinite levels so we get ready to add generated level after tutorial
                        levels.append(levelToBeAdded)
                    #skip the tutorial (only available while in the tutorial level!)
                    currentLevelNum += 1
                    currentLevel = levels[currentLevelNum]
                    levelIsClear = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_b:    # Press B to go back!
                    inSelectionMenu = True
            if (isinstance(currentLevel, endLevel)):
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    inSelectionMenu = True
                    currentLevelNum = 0 # reset the level counter
                    player.health = 100 # reset the player health
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                notLevelClearPause = True
                pause(notLevelClearPause)
                notLevelClearPause = False  # once done with the pause screen we assume it is false once again
            #implement jumping below
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if (player.numOfJumps < 2):    #can double jump
                    player.jump()
                    player.numOfJumps += 1
            if event.type == pygame.KEYDOWN and event.key == pygame.K_x:
                player.attack()
            #no longer pressing left and right arrows (the xvel should be 0)
            if event.type == pygame.KEYUP and (event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT):
                player.velX = 0
            #keep track of attacking reload time in between
            if event.type == player.attackReload:
                player.canAttack = True
            #keep track of how often alpha wolf can howl
            for mob in currentLevel.mobs:
                if (isinstance(mob, alphaWolf)):
                    if event.type == mob.howlReload:
                        mob.canHowl = True
                if (isinstance(mob, healerWolf)):
                    if event.type == mob.healerHowlReload:
                        mob.canHowl = True
                if (type(mob) == Wolf):
                    if event.type == mob.jumpReload:
                        mob.jumpReloadComplete = True
            #keep track of slash duration
            for sprite in currentLevel.allSprites:
                if (isinstance(sprite, Slash)):
                    if event.type == sprite.slashDuration:  
                        sprite.kill()
            #keep track of how long attack boost pickup lasts
            if event.type == player.damageBoostDuration:    # if the duration runs out, player is no longer damage boosted
                player.damageBoosted = False

    #live update (in game)
    if (inStartMenu == False and inSelectionMenu == False):
        currentLevel.allSprites.update() # initialize behavior of most sprites by updating first

        #test for main character collisions with platforms below, hits returns a list
        hitP = pygame.sprite.spritecollide(player, currentLevel.platforms, False) 
        mobHitP = pygame.sprite.groupcollide(currentLevel.mobs, currentLevel.platforms, False, False) 
        hitMobs = pygame.sprite.spritecollide(player, currentLevel.mobs, False, pygame.sprite.collide_mask)
        mobHitMob = pygame.sprite.groupcollide(currentLevel.mobs, currentLevel.mobs, False, False, pygame.sprite.collide_mask)
        checkFinish = pygame.sprite.spritecollide(player, currentLevel.flags, False, pygame.sprite.collide_mask)
        hitRock = pygame.sprite.spritecollide(player, currentLevel.rocks, False)
        getPickup = pygame.sprite.spritecollide(player, currentLevel.pickups, False)

        if (getPickup):
            for pickedUp in getPickup:
                pickedUp.effect()   # perform the effect of the pickup 
        if (player.damageBoosted == True):
            boostedTime = pygame.time.get_ticks() - player.startDmgBoostTimer
            if (boostedTime > dmgBoostDuration*(2/3)):
                player.damageBoostColor = red
            elif (boostedTime > dmgBoostDuration*(1/3)):
                player.damageBoostColor = yellow
            else:
                player.damageBoostColor = green
        for rock in currentLevel.rocks:
            platformRectList = []
            for platform in currentLevel.platforms:
                platformRectList.append(platform.rect)
            canDropTest = rock.dropOrNotRect.collidelist(platformRectList)
            if (player.rect.y <= platformRectList[canDropTest].y):
                rock.canDrop = True
            elif (canDropTest == -1):     # which means there is no obstacle in the way, can drop
                rock.canDrop = True
            else:
                rock.canDrop = False
        
        for mob in currentLevel.mobs:
            if (type(mob) == Wolf):
                platformRectList = []
                for platform in currentLevel.platforms:
                    platformRectList.append(platform.rect)
                canJumpTest = mob.checkAboveRect.collidelist(platformRectList)
                if (canJumpTest == -1):     # which means there is no obstacle in the way, can jump
                    mob.canJump = True
                else:
                    mob.canJump = False
            
        if (checkFinish):
            #insert a "level clear" event here 
            for mob in currentLevel.mobs:        #"poof" and kill all the mobs because level ended
                mob.poof()
            levelIsClear = True
            # AND NOW WE CONSIDER THE INFINITE MODE
            if (nonstopping == True and addedOneAlready == False):  # we add the level if the gamemode is infinite and we have not added a level yet
                batNum, wolfNum, healerNum, alphaNum = generateEnemyCounts(currentLevelNum + 1) # +1 because make decision based upon 1 level above
                spawnQuota = { "Bat":batNum, "Wolf":wolfNum, "healerWolf":healerNum, "alphaWolf":alphaNum }   # change this so the values increase after every iteration
                levelToBeAdded = normalLevel(spawnQuota, currentLevelNum + 1)    # infinite levels so we get ready to add another level
                levels.append(levelToBeAdded)  # bug (FIXED): Adds like a million levels (because constantly adding while touching flag)
                addedOneAlready = True  # because we added one level (WE SHOULDNT ADD MORE until we clear next level)

        if (hitMobs or hitRock):
            if (player.immune):         #when the level is cleared, player is immune
                player.health = player.health
            elif (player.damageable):
                if (player.health > 0):
                    if (hitMobs):
                        player.health -= hitMobs[0].damage # take off certain amount of health (based upon what monster attacked)
                        if (player.health <= 0):    # keep track of the mob that damaged the player last (cause of death)
                            lastAttackedMob = hitMobs[0]
                    elif (hitRock):
                        player.health -= hitRock[0].damage # take off certain amount of health (based upon what height dropped)
                    player.damageable = False
                    timeDamaged = pygame.time.get_ticks()
                    immuneTime = 1000
            elif (player.damageable == False):
                now = pygame.time.get_ticks()
                if (now - timeDamaged >= immuneTime):
                    player.damageable = True
        
        #artificial gravity (everytime the currentTime onesDigit less than 3 add accel)
        if (hitP == []):
            artificialGravity(player)
        # artificialGravity for mobs
        for mob in currentLevel.mobs:
            if (mob not in mobHitP):    # for the mobs that are not touching a platform
                artificialGravity(mob)

        #scroll the window when the player gets to about 20% and 80% through the window
        if (currentLevelNum != 0):
            if (player.rect.right >= screenWidth * 0.8):
                for sprite in currentLevel.allSprites:
                    sprite.rect.x -= abs(2*player.velX)
            elif (player.rect.left <= screenWidth*0.2):
                for sprite in currentLevel.allSprites:
                    sprite.rect.x += abs(2*player.velX)

        currentLevel.update()

    #Update window
    timer.tick(fps)
    pygame.display.update()

pygame.quit()