from javascript import require, On, Once, AsyncTask, once, off
import asyncio
import math

# Import the javascript libraries
mineflayer = require("mineflayer")
pathfinder_module = require('mineflayer-pathfinder')
pathfinder = pathfinder_module.pathfinder
goals = pathfinder_module.goals
Vec3 = require('vec3')
start_pos = None

# Create bot with basic parameters
bot = mineflayer.createBot(
    {"username": "ajeep", "host": "10.222.1.81", "port": 21204, "version": "1.20.4", "hideErrors": False}
)

# For Bot to load pathfinder plugin
bot.loadPlugin(pathfinder)

def fmt(x):
    return round(x, 1)

def fmt_vec3(vec):
    return f"Vec3 {{ x: {fmt(vec.x)}, y: {fmt(vec.y)}, z: {fmt(vec.z)} }}"

def get_start_pos():
    current_pos = bot.entity.position
    yaw = bot.entity.yaw
    radian_yaw = math.radians(yaw)
    dx_forward = -2 * math.sin(radian_yaw)
    dz_forward = -2 * math.cos(radian_yaw)
    start_x = current_pos.x + dx_forward
    start_z = current_pos.z + dz_forward
    start_pos = Vec3(start_x, current_pos.y - 1, start_z + 1)
    print('start_pose===', start_pos)
    return start_pos

async def perform_jumps():
    print("Bot 已成功登录，即将开始跳跃 5 秒...")
    bot.setControlState('jump', True)
    await asyncio.sleep(5)
    bot.setControlState('jump', False)
    print("Bot 已完成 5 秒跳跃。")

async def walk1(x, y, z):
    print(f"Bot 即将从当前位置开始移动到相对坐标 ({x}, {y}, {z}) 的位置...")
    current_pos = bot.entity.position
    target_pos = Vec3(current_pos.x + x, current_pos.y + y, current_pos.z - z)
    print(f"目标位置: {fmt_vec3(target_pos)}")
    goal = goals.GoalNear(target_pos.x, target_pos.y, target_pos.z, 0.1)
    try:
        goto_result = bot.pathfinder.goto(goal, timeout=20000) # Increased timeout to 20 seconds
        if asyncio.iscoroutine(goto_result):
            await goto_result
        print(f"Bot 已成功到达 {target_pos} 位置")
    except Exception as e:
        print(f"Bot 前往 {x}, {y}, {z} 位置时出错: {e}")

async def give_item_to_self(item_name, count):
    try:
        bot.chat(f'/give {bot.username} minecraft:{item_name} {count}')
        print(f"已尝试用 /give 给自己 {count} 个 {item_name}")
        await asyncio.sleep(1)
    except Exception as e:
        print(f"尝试 /give {item_name} 时出错: {e}")

async def place_torch_at_coords(x, y, z):
    # Find the block below where the torch should be placed
    block_below = bot.blockAt(Vec3(x, y - 1, z))
    if not block_below:
        print(f"无法在 ({x},{y},{z}) 放置火把: 下方没有方块支撑。")
        return

    # Wait for torch to be in inventory
    torch_item = None
    retries = 0
    max_retries = 10 # Try for up to 10 * 0.5 = 5 seconds
    while torch_item is None and retries < max_retries:
        torch_item = bot.inventory.findInventoryItem('torch', None)
        if torch_item is None:
            print(f"等待火把出现在物品栏中... (尝试 {retries + 1}/{max_retries})")
            await asyncio.sleep(0.5)
            retries += 1

    if not torch_item:
        print("物品栏中没有找到火把，无法放置。")
        return

    # Equip torch
    bot.equip(torch_item, 'hand')
    await asyncio.sleep(3) # Small delay after equipping

    try:
        # Place the torch on the block below, facing upwards
        bot.placeBlock(block_below, Vec3(0, 1, 0)) # Place on top of the block_below
        print(f"已在 ({x},{y},{z}) 放置火把。")
    except Exception as e:
        print(f"在 ({x},{y},{z}) 放置火把时出错: {e}")

async def build_my_house(length, width, height, block_type='oak_planks'):
    global start_pos
    print(f"开始建造长{length}宽{width}高{height}的房子...")

    # Ensure bot has enough blocks
    await give_item_to_self(block_type, length * width * height)
    await asyncio.sleep(1) # Give server time to process /give command

    # Calculate absolute coordinates for the house
    # start_pos is the bottom-front-left corner of the house
    x1 = int(start_pos.x)
    y1 = int(start_pos.y)
    z1 = int(start_pos.z)
    x2 = int(start_pos.x + length - 1)
    y2 = int(start_pos.y + height - 1)
    z2 = int(start_pos.z + width - 1)

    print(f"House coordinates: ({x1},{y1},{z1}) to ({x2},{y2},{z2})")

    try:
        # Floor
        bot.chat(f'/fill {x1} {y1} {z1} {x2} {y1} {z2} {block_type}')
        await asyncio.sleep(0.5)

        # Walls (hollow structure)
        # Front wall
        bot.chat(f'/fill {x1} {y1+1} {z1} {x2} {y2} {z1} {block_type}')
        await asyncio.sleep(0.5)
        # Back wall
        bot.chat(f'/fill {x1} {y1+1} {z2} {x2} {y2} {z2} {block_type}')
        await asyncio.sleep(0.5)
        # Left wall
        bot.chat(f'/fill {x1} {y1+1} {z1+1} {x1} {y2} {z2-1} {block_type}')
        await asyncio.sleep(0.5)
        # Right wall
        bot.chat(f'/fill {x2} {y1+1} {z1+1} {x2} {y2} {z2-1} {block_type}')
        await asyncio.sleep(0.5)

        # Create door opening (1 block wide, 2 blocks high) in the front wall
        # The door will be centered along the length (x-axis)
        door_x = int(start_pos.x + length // 2 - 1)
        bot.chat(f'/fill {door_x} {y1+1} {z1} {door_x} {y1+2} {z1} air')
        await asyncio.sleep(0.5)

        # Ceiling
        bot.chat(f'/fill {x1} {y2} {z1} {x2} {y2} {z2} {block_type}')
        await asyncio.sleep(0.5)

        print("房子建造完成！")
    except Exception as e:
        print(f"建造房子时出错: {e}")

# Login event required for bot
@On(bot, "login")
def login(this):
    print("Bot 已成功登录 Minecraft 服务器。")
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async def main_task():
        global start_pos
        await perform_jumps()
        # Move forward a bit to have space for the house
        await walk1(0, 0, 5)
        start_pos = get_start_pos()
        # Build a house of 10 long, 6 wide, 6 high
        await build_my_house(10, 6, 6, 'oak_planks')

        # Move bot inside the house
        # The door is at x = start_pos.x + length // 2 - 1, y = start_pos.y + 1 to y + 2, z = start_pos.z
        # Move to the center of the door and then inside
        door_x_offset = 10 // 2 - 1 # Relative x-offset for the door
        await walk1(door_x_offset, 0, -1) # Move to the door opening (relative to current bot position)
        await walk1(0, 0, -2) # Move inside the house (relative to current bot position)

        # Give bot 10 torches
        await give_item_to_self('torch', 10)
        await asyncio.sleep(2) # Give server more time to process /give command and update inventory

        # Place torches inside the house
        # Torch 1: Near front-left corner
        await place_torch_at_coords(int(start_pos.x + 2), int(start_pos.y + 1), int(start_pos.z + 2))
        await asyncio.sleep(0.5)

        # Torch 2: Near back-right corner
        await place_torch_at_coords(int(start_pos.x + 10 - 3), int(start_pos.y + 1), int(start_pos.z + 6 - 3))
        await asyncio.sleep(0.5)

        # Torch 3: Near front-right corner
        await place_torch_at_coords(int(start_pos.x + 10 - 3), int(start_pos.y + 1), int(start_pos.z + 2))
        await asyncio.sleep(0.5)

        # Torch 4: Near back-left corner
        await place_torch_at_coords(int(start_pos.x + 2), int(start_pos.y + 1), int(start_pos.z + 6 - 3))
        await asyncio.sleep(0.5)

        loop.call_soon(loop.stop)

    loop.create_task(main_task())
    if not loop.is_running():
        loop.run_forever()

@On(bot, "kicked")
def kicked(this, reason, loggedIn):
    print(f"被踢出: {reason}")

@On(bot, "error")
def error(this, err):
    print(f"连接错误: {err}")
