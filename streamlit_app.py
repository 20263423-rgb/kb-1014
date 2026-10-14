import random
import math
import time
from pathlib import Path

import streamlit as st


st.set_page_config(page_title='두더지 잡기 게임', page_icon='🐹')

st.title('두더지 잡기 게임')
st.write('두더지를 클릭해 보세요!')

image_folder = Path(__file__).parent


@st.cache_data
def load_image(image_path):
    return Path(image_path).read_bytes()


hole_image = load_image(str(image_folder / 'hole.png'))
mole_image = load_image(str(image_folder / 'img.png'))

GAME_DURATION_SECONDS = 60
MOLE_DURATION_SECONDS = 1.5


def reset_game():
    st.session_state.game_state = 'ready'
    st.session_state.score = 0
    st.session_state.lives = 3
    st.session_state.remaining_seconds = GAME_DURATION_SECONDS
    st.session_state.game_started_at = None
    st.session_state.mole_position = None
    st.session_state.mole_number = 0
    st.session_state.last_processed_mole_number = 0
    st.session_state.mole_spawned_at = None
    st.session_state.message = ''


if 'game_state' not in st.session_state:
    reset_game()


def start_game():
    reset_game()
    now = time.monotonic()
    st.session_state.game_state = 'playing'
    st.session_state.game_started_at = now
    spawn_mole(now)


def finish_game(now):
    st.session_state.game_state = 'finished'
    st.session_state.mole_position = None
    st.session_state.mole_spawned_at = None


def spawn_mole(now):
    previous_position = st.session_state.mole_position
    possible_positions = [position for position in range(9) if position != previous_position]
    st.session_state.mole_position = random.choice(possible_positions)
    st.session_state.mole_number += 1
    st.session_state.mole_spawned_at = now


def remaining_time_at(now):
    elapsed = now - st.session_state.game_started_at
    return max(0, math.ceil(GAME_DURATION_SECONDS - elapsed))


def process_mole(mole_number, caught, now):
    if (
        st.session_state.game_state != 'playing'
        or mole_number != st.session_state.mole_number
        or mole_number == st.session_state.last_processed_mole_number
    ):
        return

    if now - st.session_state.game_started_at >= GAME_DURATION_SECONDS:
        st.session_state.remaining_seconds = 0
        finish_game(now)
        return

    if now - st.session_state.mole_spawned_at >= MOLE_DURATION_SECONDS:
        caught = False

    st.session_state.last_processed_mole_number = mole_number
    previous_position = st.session_state.mole_position

    if caught:
        st.session_state.score += 10
        st.session_state.message = '두더지를 잡았습니다! +10점'
    else:
        st.session_state.lives = max(0, st.session_state.lives - 1)
        st.session_state.message = '시간이 지나 라이프가 1 줄었습니다.'

    if st.session_state.lives == 0:
        st.session_state.remaining_seconds = remaining_time_at(now)
        finish_game(now)
    else:
        spawn_mole(now)


def update_game(now):
    if st.session_state.game_state != 'playing':
        return

    st.session_state.remaining_seconds = remaining_time_at(now)
    if st.session_state.remaining_seconds == 0:
        finish_game(now)
        return

    if st.session_state.lives == 0:
        finish_game(now)
        return

    if now - st.session_state.mole_spawned_at >= MOLE_DURATION_SECONDS:
        process_mole(st.session_state.mole_number, caught=False, now=now)


def handle_hole_click(hole_index, displayed_mole_number):
    now = time.monotonic()
    update_game(now)

    if (
        st.session_state.game_state != 'playing'
        or displayed_mole_number != st.session_state.mole_number
    ):
        return

    if hole_index == st.session_state.mole_position:
        process_mole(displayed_mole_number, caught=True, now=now)
    else:
        st.session_state.message = ''


@st.fragment(run_every=0.1)
def render_game():
    now = time.monotonic()
    update_game(now)

    score_column, lives_column, time_column = st.columns(3)
    with score_column:
        st.metric('현재 점수', st.session_state.score)
    with lives_column:
        st.metric('라이프', st.session_state.lives)
    with time_column:
        st.metric('남은 시간', st.session_state.remaining_seconds)

    if st.session_state.game_state == 'ready':
        st.button('게임 시작', key='start_game', on_click=start_game, width='stretch')
    elif st.session_state.game_state == 'finished':
        st.success(f'게임 종료! 최종 점수: {st.session_state.score}점')
        st.button('다시 시작', key='restart_game', on_click=reset_game, width='stretch')
    else:
        elapsed = now - st.session_state.mole_spawned_at
        st.caption(f'두더지 #{st.session_state.mole_number} · 등장 후 {elapsed:.1f}초')

    for row in range(3):
        columns = st.columns(3)
        for column_index, column in enumerate(columns):
            hole_index = row * 3 + column_index
            with column:
                image = mole_image if hole_index == st.session_state.mole_position else hole_image
                st.image(image, width='stretch')
                st.button(
                    f'구멍 {hole_index + 1}',
                    key=f'hole_{hole_index}',
                    on_click=handle_hole_click,
                    args=(hole_index, st.session_state.mole_number),
                    width='stretch',
                    disabled=st.session_state.game_state != 'playing',
                )

    if st.session_state.message:
        st.success(st.session_state.message)


render_game()
