# app/discord/application_process/helpers.py
import io
import os
from datetime import datetime

import discord

from app.models.form_response import FormResponse, InterviewStatus
from app.models.staff import Staff
from app.utils.redis_client import redis_client

APPLY_FORM_CHANNEL_ID = int(os.getenv("APPLY_FORM_CHANNEL_ID"))
APPLY_LOG_CHANNEL_ID = int(os.getenv("APPLY_LOG_CHANNEL_ID"))


def truncate(value, max_length=1024):
    """Truncate a string to the specified maximum length."""
    if len(value) > max_length:
        return value[: max_length - 80] + "...（過長無法顯示）"
    return value


def get_bot():
    """Retrieve the bot instance from the global scope."""
    from app.discord.bot_module import bot

    return bot


def get_embed_color(interview_status):
    """Return the color for the embed based on the interview status."""
    status_colors = {
        InterviewStatus.NOT_ACCEPTED: 0xFF0000,  # Red
        InterviewStatus.NOT_CONTACTED: 0xFF4500,  # Orange
        InterviewStatus.EMAIL_SENT: 0xFF4500,  # Orange
        InterviewStatus.INTERVIEW_SCHEDULED: 0x3498DB,  # Blue
        InterviewStatus.NO_SHOW: 0xE74C3C,  # Red
        InterviewStatus.INTERVIEW_FAILED: 0xE74C3C,  # Red
        InterviewStatus.CANCELLED: 0xE74C3C,  # Red
        InterviewStatus.INTERVIEW_PASSED_WAITING_MANAGER_FORM: 0x9B59B6,  # Purple
        InterviewStatus.INTERVIEW_PASSED_WAITING_FOR_FORM: 0x9B59B6,  # Purple
        InterviewStatus.INTERVIEW_PASSED: 0x2ECC71,  # Green
        InterviewStatus.TRANSFERRED_TO_ANOTHER_TEAM: 0xF1C40F,  # Yellow
    }
    return status_colors.get(interview_status, 0x95A5A6)  # Default gray


async def send_initial_embed(form_response: FormResponse):
    """Send the initial embed to the apply form channel."""
    bot = get_bot()
    await bot.wait_until_ready()
    channel = bot.get_channel(APPLY_FORM_CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {APPLY_FORM_CHANNEL_ID} not found.")
        return

    # Create the embed
    embed = discord.Embed(
        title="新申請：等待受理",
        description="有一個新的申請等待受理。",
        color=get_embed_color(form_response.interview_status),
        timestamp=datetime.utcnow(),
    )

    # Add fields to the embed
    fields = [
        ("申請識別碼", str(form_response.uuid)),
        ("申請狀態", form_response.interview_status.value),
        ("姓名", form_response.name),
        ("電子郵件", form_response.email),
        ("電話號碼", form_response.phone_number),
        ("高中階段", form_response.high_school_stage),
        ("城市", form_response.city),
        ("申請組別", ", ".join(form_response.interested_fields)),
        ("順序偏好", form_response.preferred_order),
        ("選擇原因", form_response.reason_for_choice),
    ]

    if form_response.related_experience:
        fields.append(("相關經驗", form_response.related_experience))

    for name, value in fields:
        if value:
            value = truncate(str(value))
            embed.add_field(name=name, value=value, inline=False)

    # Create a text attachment with full content
    full_content = ""
    for name, value in fields:
        if value:
            full_content += f"{name}: {value}\n"

    # Using io.StringIO for file attachment
    file_stream = io.StringIO(full_content)

    file = discord.File(
        fp=file_stream,
        filename=f"application_{form_response.uuid}.txt",
    )

    # Create view with buttons
    from .views import AcceptOrCancelView

    view = AcceptOrCancelView(form_response)

    await channel.send(embed=embed, file=file, view=view)


async def send_log_message(form_response: FormResponse, title: str):
    """Send a log message to the APPLY_LOG_CHANNEL_ID channel."""
    bot = get_bot()
    await bot.wait_until_ready()
    channel = bot.get_channel(APPLY_LOG_CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {APPLY_LOG_CHANNEL_ID} not found.")
        return

    # Create the embed
    embed = discord.Embed(
        title=title,
        description="申請流程已更新。",
        color=get_embed_color(form_response.interview_status),
        timestamp=datetime.utcnow(),
    )

    # Add fields to the embed
    fields = [
        ("申請識別碼", str(form_response.uuid)),
        ("申請狀態", form_response.interview_status.value),
        ("姓名", form_response.name),
        ("電子郵件", form_response.email),
        ("電話號碼", form_response.phone_number),
        ("高中階段", form_response.high_school_stage),
        ("城市", form_response.city),
        ("申請組別", ", ".join(form_response.interested_fields)),
        ("順序偏好", form_response.preferred_order),
        ("選擇原因", form_response.reason_for_choice),
    ]

    if form_response.related_experience:
        fields.append(("相關經驗", form_response.related_experience))

    for name, value in fields:
        if value:
            value = truncate(str(value))
            embed.add_field(name=name, value=value, inline=False)

    # Add history
    if form_response.history:
        history_str = "\n".join(form_response.history)
        embed.add_field(name="歷史紀錄", value=history_str, inline=False)

    # Create a text attachment with full content
    full_content = ""
    for name, value in fields:
        if value:
            full_content += f"{name}: {value}\n"
    if form_response.history:
        full_content += "\n歷史紀錄:\n" + "\n".join(form_response.history)

    file = discord.File(
        fp=bytes(full_content, encoding="utf-8"),
        filename=f"application_{form_response.uuid}_details.txt",
    )

    await channel.send(embed=embed, file=file)