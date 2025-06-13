import os
import discord
import pandas as pd
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


# .env の読み込み
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Intents の設定
intents = discord.Intents.default()
intents.members = True  # メンバー情報取得を有効化
intents.message_content = True # メッセージ内容取得を有効化

class CustomHelpCommand(commands.HelpCommand):

    def __init__(self):
        super().__init__(
            command_attrs={"brief": "ヘルプを表示"}
        )

    async def send_bot_help(self, mapping):
        #Embedの作成
        e = discord.Embed(
            title="ヘルプ", 
            description="利用可能なコマンド一覧"
        )
        
        cmds = mapping[None]
        
        for command in await self.filter_commands(cmds):
            e.add_field(name=command.name, value=f'> {command.brief}', inline=False)
        
        await self.get_destination().send(embed=e)

bot = commands.Bot(
    command_prefix='!', 
    intents=intents,
    help_command=CustomHelpCommand()
)

#bot初期化
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

#!getコマンドの定義
@bot.command(
        name='get', 
        brief='メンバー情報を取してCSVに出力'
    )

#コマンド実行者の権限チェック
@commands.has_role("Moderator") #"Moderator"の部分は実際のロール名に置き換え

#情報の取得とCSV変換
async def export_members(ctx):
    guild: discord.Guild = ctx.guild
    data = []

    # メンバーをループ
    async for member in guild.fetch_members(limit=None):
        username = member.display_name # ユーザー名取得(ニックネーム)

        # UTC から JSTに変換
        if member.joined_at:
            joined_at = member.joined_at.astimezone(ZoneInfo('Asia/Tokyo'))
        else:
            joined_at = datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Tokyo'))

        # ロール名のリスト（@everyone を除外）
        roles = [r.name for r in member.roles if r.name != "@everyone"]
        data.append({
            'ユーザー名': username,
            '参加日時': joined_at.strftime('%Y-%m-%d %H:%M:%S'),
            'ロール': ";".join(roles)
        })

    # pandas で DataFrame 化 & CSV 出力
    df = pd.DataFrame(data)
    # CSV ファイル名に現在時刻を使う
    timestamp = datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Tokyo'))
    formatted_time = timestamp.strftime('%Y%m%d%H%M%S')
    csv_path = f'members_{guild.id}_{formatted_time}.csv'
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    # ファイルを Discord に送信
    await ctx.send(file=discord.File(csv_path))
    # ローカル保存を残す場合はコメントアウトを外す
    # print(f'Saved to {csv_path}')

# エラーハンドリング
@export_members.error
async def export_members_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('このコマンドを使用する権限がありません。管理者に連絡してください。')
    else:
        await ctx.send(f'エラーが発生しました: {error}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("存在しないコマンドです。`!help`でコマンドを確認してください。")
    else:
        raise error

bot.run(TOKEN)
