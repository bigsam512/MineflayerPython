from javascript import require, On
import asyncio
from common_bot_utils import (
    fmt, fmt_vec3, get_start_pos, perform_jumps, equip_item, walk1,
    place_on_block, place_components, plug_component, place_entity_on_block,
    toggle_block, kicked, error, Vec3
)

mineflayer = require("mineflayer")
pathfinder_module = require('mineflayer-pathfinder')
pathfinder = pathfinder_module.pathfinder
goals = pathfinder_module.goals

start_pos = None

bot = mineflayer.createBot({
    "username": "bigsam",
    "host": "localhost",
    "port": 25565,
    "auth": 'offline',
    "version": "1.20.4",
    "hideErrors": False
})

bot.loadPlugin(pathfinder)

async def give_item_to_self(item_name, count):
    try:
        bot.chat(f'/give {bot.username} minecraft:{item_name} {count}')
        print(f"已尝试用 /give 给自己 {count} 个 {item_name}")
        await asyncio.sleep(1)
    except Exception as e:
        print(f"尝试 /give {item_name} 时出错: {e}")

async def perform_dig(blocks=[]):
    global start_pos
    print("Bot 即将挖坑...")
    await equip_item(bot, 'diamond_shovel', 'hand')
    for x_offset, y_offset, z_offset in blocks:
        print(f"尝试挖掘方块: {x_offset}, 0, {z_offset}, {fmt(start_pos.x + x_offset)}, {fmt(start_pos.y + y_offset)}, {fmt(start_pos.z - z_offset)}")
        block_pos = Vec3(start_pos.x + x_offset, start_pos.y + y_offset, start_pos.z - z_offset)
        block = bot.blockAt(block_pos)
        if block:
            try:
                dig_result = bot.dig(block)
                if asyncio.iscoroutine(dig_result):
                    await dig_result
            except Exception as e:
                print(f"挖掘方块 {block_pos} 时出错: {e}")
    print("Bot 已完成挖坑。")

async def pour_water_in_hole(relative_x, relative_y, relative_z):
    """Pours water at a location relative to the bot without moving."""
    print("开始向坑里倒水...")

    bot_pos = bot.entity.position
    look_at_point = bot_pos.offset(relative_x, relative_y, relative_z)

    try:
        # 1. Equip the water bucket.
        await equip_item(bot, 'water_bucket', 'hand')
        print("已装备水桶。")
        await asyncio.sleep(0.5)

        # 2. Look at the target point to pour water.
        print(f"看着目标点 {fmt_vec3(look_at_point)} 倒水...")
        bot.lookAt(look_at_point)
        await asyncio.sleep(0.2) # Give bot time to look

        # 3. Activate the item (water bucket) to pour water.
        activate_result = bot.activateItem()
        if asyncio.iscoroutine(activate_result):
            await activate_result

        print("✅ 已成功将水倒入坑中。")
        await asyncio.sleep(1.0)

    except Exception as e:
        print(f"❌ 倒水时出错: {e}")

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
        await perform_jumps(bot)
        await walk1(bot, 0, 0, 10)
        await give_item_to_self('chest', 10)
        await give_item_to_self('hopper', 10)
        await give_item_to_self('rail', 10)
        await give_item_to_self('powered_rail', 10)
        await give_item_to_self('oak_planks', 45)
        await give_item_to_self('redstone_block', 5)
        await give_item_to_self('grass_block', 20)
        await give_item_to_self('water_bucket', 5)
        start_pos = get_start_pos(bot)
        components_to_place = [
            ("chest", 0, 1, 0)
        ]
        await place_components(bot, start_pos, components_to_place)
        await walk1(bot, 1, 0, 0)
        await place_components(bot, start_pos, [("chest", 1, 1, 0)])
        await walk1(bot, -1, 0, 6)

        bot.setControlState('sneak', True)
        await plug_component(bot, start_pos, "hopper", 0, 1, 0, Vec3(0, 0, -1))
        await plug_component(bot, start_pos, "hopper", 0, 1, 1, Vec3(0, 0, -1))
        await plug_component(bot, start_pos, "hopper", 0, 1, 2, Vec3(-1, 0, 0))
        await plug_component(bot, start_pos, "hopper", -1, 1, 2, Vec3(-1, 0, 0))
        await plug_component(bot, start_pos, "hopper", 0, 1, 2, Vec3(1, 0, 0))
        await plug_component(bot, start_pos, "hopper", 1, 1, 2, Vec3(1, 0, 0))
        components_to_place = [
            ("powered_rail", -2, 2, 2),
            ("rail", -1, 2, 2),
            ("rail", 0, 2, 2),
            ("rail", 1, 2, 2),
            ("powered_rail", 2, 2, 2),
            ("oak_planks", -3, 1, 2),
            ("oak_planks", -3, 2, 2),
            ("oak_planks", 3, 1, 2),
            ("oak_planks", 3, 2, 2),
            ("oak_planks", -3, 1, 3),
            ("oak_planks", -3, 2, 3),
            ("oak_planks", 3, 1, 3),
            ("oak_planks", 3, 2, 3),
            ("oak_planks", -2, 1, 3),
            ("redstone_block", -2, 2, 3),
            ("oak_planks", -1, 1, 3),
            ("oak_planks", -1, 2, 3),
            ("oak_planks", 2, 1, 3),
            ("redstone_block", 2, 2, 3),
            ("oak_planks", 1, 1, 3),
            ("oak_planks", 1, 2, 3),
            ("oak_planks", 0, 1, 3),
            ("oak_planks", 0, 2, 3),
        ]
        await place_components(bot, start_pos, components_to_place)

        components_to_place = [
            ("grass_block", -3, 1, 4)
        ]
        await place_components(bot, start_pos, components_to_place)
        await walk1(bot, 0, 2, -2)
        components_to_place = [
            ("grass_block", -2, 3, 2),
            ("grass_block", -1, 3, 2),
            ("grass_block", 0, 3, 2),
            ("grass_block", 1, 3, 2),
            ("grass_block", 2, 3, 2),
            ("oak_planks", 3, 3, 3),
            ("oak_planks", -3, 3, 3),
            ("oak_planks", -3, 3, 2),
            ("oak_planks", 3, 3, 2),
        ]
        await place_components(bot, start_pos, components_to_place)
        await plug_component(bot, start_pos, "oak_planks", -3, 3, 2, Vec3(0, 0, 1))
        await plug_component(bot, start_pos, "oak_planks", -2, 3, 2, Vec3(0, 0, 1))
        await plug_component(bot, start_pos, "oak_planks", -1, 3, 2, Vec3(0, 0, 1))
        await plug_component(bot, start_pos, "oak_planks", 0, 3, 2, Vec3(0, 0, 1))
        await plug_component(bot, start_pos, "oak_planks", 1, 3, 2, Vec3(0, 0, 1))
        await plug_component(bot, start_pos, "oak_planks", 2, 3, 2, Vec3(0, 0, 1))
        await plug_component(bot, start_pos, "oak_planks", 3, 3, 2, Vec3(0, 0, 1))
        await plug_component(bot, start_pos, "oak_planks", -3, 3, 3, Vec3(0, 0, -1))
        await plug_component(bot, start_pos, "oak_planks", -3, 3, 4, Vec3(1, 0, 0))
        await plug_component(bot, start_pos, "oak_planks", -2, 3, 4, Vec3(1, 0, 0))
        await plug_component(bot, start_pos, "oak_planks", -1, 3, 4, Vec3(1, 0, 0))
        await plug_component(bot, start_pos, "oak_planks", 0, 3, 4, Vec3(1, 0, 0))
        await plug_component(bot, start_pos, "oak_planks", 1, 3, 4, Vec3(1, 0, 0))
        await plug_component(bot, start_pos, "oak_planks", 2, 3, 4, Vec3(1, 0, 0))
        await walk1(bot, 0, 1, -1)
        await pour_water_in_hole(-2, -1, -1)
        await pour_water_in_hole(-1, -1, -1)
        await pour_water_in_hole(0, -1, -1)
        await pour_water_in_hole(1, -1, -1)
        await pour_water_in_hole(2, -1, -1)
        loop.call_soon(loop.stop)

    loop.create_task(main_task())
    if not loop.is_running():
        loop.run_forever()

bot.on("kicked", lambda this_arg, reason, loggedIn: kicked(this_arg, reason, loggedIn))
bot.on("error", lambda this_arg, err: error(this_arg, err))
