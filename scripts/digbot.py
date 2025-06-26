from javascript import require, On
import asyncio
import math

mineflayer = require("mineflayer")
# 加载路径查找插件
pathfinder_module = require('mineflayer-pathfinder')
# 获取实际的插件函数
pathfinder = pathfinder_module.pathfinder
# 获取目标模块
goals = pathfinder_module.goals
Vec3 = require('vec3')
start_pos = None

bot = mineflayer.createBot({
    "username": "bigsam",
    "host": "192.168.1.82",
    "port": 25565,
    "auth": 'offline',
    "version": "1.20.4",
    "hideErrors": False
})

# 为 Bot 加载路径查找插件
bot.loadPlugin(pathfinder)

def fmt(x):
    return round(x, 1)

def fmt_vec3(vec):
    return f"Vec3 {{ x: {fmt(vec.x)}, y: {fmt(vec.y)}, z: {fmt(vec.z)} }}"

def get_start_pos():
    # 获取当前 Bot 的位置和朝向
    current_pos = bot.entity.position
    yaw = bot.entity.yaw
    # 将角度转换为弧度
    radian_yaw = math.radians(yaw)
    # 计算向前两格的偏移量
    dx_forward = -2 * math.sin(radian_yaw)
    dz_forward = -2 * math.cos(radian_yaw)
    # 确定挖坑的起始位置，在 Bot 前方两格开始
    start_x = current_pos.x + dx_forward
    start_z = current_pos.z + dz_forward
    start_pos = Vec3(start_x, current_pos.y - 1, start_z + 1)
    print('start_pose===', start_pos)
    return start_pos

# 定义一个辅助函数来处理异步跳跃逻辑，让 Bot 跳 5 秒
async def perform_jumps():
    print("Bot 已成功登录，即将开始跳跃 5 秒...")
    bot.setControlState('jump', True)  # 设置跳跃状态为开启
    await asyncio.sleep(5)  # 等待 5 秒
    bot.setControlState('jump', False)  # 设置跳跃状态为关闭
    print("Bot 已完成 5 秒跳跃。")

# 通用装备函数：将任意物品装备到指定手
async def equip_item(item_name, hand='hand'):
    item = bot.inventory.findInventoryItem(item_name, None)
    if item:
        #print(f"已找到 {item_name}，物品信息：{item}")
        try:
            equip_result = bot.equip(item, hand)
            if asyncio.iscoroutine(equip_result):
                await equip_result
            print(f"已成功将 {item_name} 装备到 {hand}")
        except Exception as e:
            print(f"装备 {item_name} 到 {hand} 时出错: {e}")
    else:
        print(f"物品栏中没有找到 {item_name}")

async def perform_dig(blocks=[]):
    global start_pos
    print("Bot 即将挖坑...")
    await equip_item('diamond_shovel', 'hand')
    for x_offset, y_offset, z_offset in blocks:
        print(f"尝试挖掘方块: {x_offset}, 0, {z_offset}, {fmt(start_pos.x + x_offset)}, {fmt(start_pos.y + y_offset)}, {fmt(start_pos.z - z_offset)}")
        block_pos = Vec3(start_pos.x + x_offset, start_pos.y + y_offset, start_pos.z - z_offset)
        block = bot.blockAt(block_pos)
        if block:
            try:
                # 尝试挖掘方块
                dig_result = bot.dig(block)
                if asyncio.iscoroutine(dig_result):
                    await dig_result
            except Exception as e:
                print(f"挖掘方块 {block_pos} 时出错: {e}")
    print("Bot 已完成挖坑。")

# 辅助函数：让 Bot 从当前位置开始移动到相对坐标位置
async def walk1(x, y, z):
    print(f"Bot 即将从当前位置开始移动到相对坐标 ({x}, {y}, {z}) 的位置...")
    current_pos = bot.entity.position
    target_pos = Vec3(current_pos.x + x, current_pos.y + y, current_pos.z - z)
    print(f"目标位置: {fmt_vec3(target_pos)}")
    goal = goals.GoalNear(target_pos.x, target_pos.y, target_pos.z, 0.1)
    try:
        goto_result = bot.pathfinder.goto(goal)
        if asyncio.iscoroutine(goto_result):
            await goto_result
        print(f"Bot 已成功到达 {target_pos} 位置")
    except Exception as e:
        print(f"Bot 前往 {x}, {y}, {z} 位置时出错: {e}")

# 通用放置函数：可顶面/侧面/底面/实体一体化
async def place_on_block(item_name, x, y, z, direction_vec=Vec3(0,1,0), support_offset=Vec3(0,-1,0), block_type=None, max_retries=3, skip_air_check=False):
    global start_pos
    abs_x = start_pos.x + x + support_offset.x
    abs_y = start_pos.y + y + support_offset.y
    abs_z = start_pos.z - z + support_offset.z
    block = bot.blockAt(Vec3(abs_x, abs_y, abs_z))
    if not block:
        print(f"({fmt(abs_x)},{fmt(abs_y)},{fmt(abs_z)}) 没有支撑方块，无法放置 {item_name}")
        return
    if block_type and block_type not in block.name:
        print(f"({fmt(abs_x)},{fmt(abs_y)},{fmt(abs_z)}) 不是 {block_type}，实际是 {block.name}，无法放置 {item_name}")
        return
    item = bot.inventory.findInventoryItem(item_name, None)
    if not item:
        print(f"物品栏中没有 {item_name}")
        return
    equip_result = bot.equip(item, 'hand')
    if asyncio.iscoroutine(equip_result):
        await equip_result
    # 检查目标插入位置是否为空气（仅对侧插/底插等特殊情况有用，放矿车时跳过）
    if not skip_air_check:
        target_pos = Vec3(abs_x + direction_vec.x, abs_y + direction_vec.y, abs_z + direction_vec.z)
        target_block = bot.blockAt(target_pos)
        if target_block and target_block.name != 'air':
            print(f"警告：目标插入位置已被 {target_block.name} 占用，无法插入！")
            return
    for retry in range(max_retries):
        try:
            result = bot.placeBlock(block, direction_vec)
            if asyncio.iscoroutine(result):
                await result
            print(f"已成功将 {item_name} 放在 {fmt_vec3(block.position)} 的方向 {fmt_vec3(direction_vec)}")
            break
        except Exception as e:
            if "blockUpdate" in str(e):
                print(f"放置 {item_name} 可能已成功，但未收到 blockUpdate 事件（可忽略此错误），详情: {e}")
                break
            else:
                print(f"第 {retry+1} 次尝试放置 {item_name} 失败: {e}")

# 兼容原有接口的适配器
async def place_components(components_to_place=None):
    for item_info in components_to_place:
        item_name, x_offset, y_offset, z_offset = item_info[:4]
        await place_on_block(item_name, x_offset, y_offset, z_offset, direction_vec=Vec3(0,1,0), support_offset=Vec3(0,-1,0))

async def plug_component(item_name, x, y, z, direction_vec):
    await place_on_block(item_name, x, y, z, direction_vec=direction_vec, support_offset=Vec3(0,0,0))

async def place_entity_on_block(item_name, x, y, z, block_type=None):
    # 放置矿车等实体时跳过空气检测，否则 observer 上的 rail 无法放矿车
    await place_on_block(item_name, x, y, z, direction_vec=Vec3(0,1,0), support_offset=Vec3(0,0,0), block_type=block_type, skip_air_check=True)


async def toggle_block(block_type, x, y, z):
    global start_pos
    x=start_pos.x+x
    y=start_pos.y+y
    z=start_pos.z-z
    block = bot.blockAt(Vec3(x, y, z))
    if block and block.name == block_type:
        bot.activateBlock(block)
        print(f"已激活 {block_type} at {fmt_vec3(block.position)}")
    else:
        print(f"未找到 {block_type} at {fmt(x)},{fmt(y)},{fmt(z)}")


# 非异步的事件处理函数
@On(bot, "login")
def login(this):
    print("Bot 已成功登录 Minecraft 服务器。")
    # 获取主事件循环
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async def main_task():
        global start_pos
        await perform_jumps()
        await walk1(0, 0, 5)
        start_pos=get_start_pos()
        blocks=[(0,0,0),(1,0,0),(2,0,0),(0,0,1),(1,0,1),(2,0,1),(2,0,2)]
        await perform_dig(blocks)
        await walk1(3, 0, 1)
        components_to_place = [
            ("piston", 2, 0, 2),
            ("smooth_stone", 2, 0, 1)
        ]
        await place_components(components_to_place)

        await plug_component("redstone_torch", 2, 0, 1, Vec3(0, 0, 1))

        components_to_place = [
            ("smooth_stone", 2, 1, 0),
            ("redstone_torch", 2, 2, 0),
            ("smooth_stone", 2, 3, 0)
        ]
        await place_components(components_to_place)
        await walk1(0, 0, 2)
        await plug_component("smooth_stone", 2, 3, 0, Vec3(0, 0, -1))
        await plug_component("smooth_stone", 2, 3, 1, Vec3(0, 0, -1))
        components_to_place = [
            ("redstone", 2, 4, 0),
            ("redstone", 2, 4, 1),
            ("smooth_stone", 2, 4, 2),
            ("smooth_stone", 2, 5, 2)
        ]
        await place_components(components_to_place)
        blocks=[(2,3,2),(2,4,2)]
        await perform_dig(blocks)
        await plug_component("piston", 2, 5, 2, Vec3(0, -1, 0))
        await walk1(-4, 0, -1)
        components_to_place = [
            ("redstone", 1, 0, 0),
            ("redstone", 0, 0, 0),
            ("redstone", 0, 0, 1),
            ("repeater", 1, 0, 1),
        ]
        await place_components(components_to_place)
        await plug_component("lever", 2, 1, 0, Vec3(-1, 0, 0))
        await toggle_block("lever", 1, 1, 0)
        await toggle_block("repeater", 1, 0, 1)

        components_to_place = [
            ("smooth_stone", 1, 1, 2)
        ]
        await place_components(components_to_place)
        await walk1(2, 2, 2)
        await plug_component("observer", 2, 1, 2, Vec3(0, 1, 0))
        await plug_component("rail", 2, 2, 2, Vec3(0, 1, 0))
        await place_entity_on_block("hopper_minecart", 2, 3, 2, block_type="rail")
        await walk1(-2, 0, -2)
        await toggle_block("lever", 1, 1, 0)
        # 手动停止事件循环
        loop.call_soon(loop.stop)

    # 将 main_task 协程放入事件循环中执行
    loop.create_task(main_task())
    if not loop.is_running():
        loop.run_forever()

@On(bot, "kicked")
def kicked(this, reason, loggedIn):
    print(f"被踢出: {reason}")

@On(bot, "error")
def error(this, err):
    print(f"连接错误: {err}")
