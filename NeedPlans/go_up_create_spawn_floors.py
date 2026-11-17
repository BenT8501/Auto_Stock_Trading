# -*- coding: utf-8 -*-
r"""UEFN 에디터에서 GO ~! UP!!!! 시작 바닥과 Player Spawn을 생성한다.

준비
1. 맵에 사용할 Floor 한 장과 실제 Player Spawn Pad 장치 한 개를 배치한다.
2. Outliner의 이름(Actor Label)을 아래와 같이 바꾼다.
   Floor: GOUP_Floor_Template
   Player Spawn Pad: GOUP_PlayerSpawn_Template
3. Floor 원본의 회전을 0으로 맞춘다. 원하는 크기·충돌·재질을 설정한다.
4. UEFN의 Python Editor Scripting을 활성화한 환경에서 이 파일을 실행한다.
   Python 콘솔 예:
   exec(compile(open(r'C:\WorkSpace\Auto_Stock_Trading\NeedPlans\go_up_create_spawn_floors.py', encoding='utf-8').read(), 'go_up_create_spawn_floors.py', 'exec'))

결과
- A~I 각 지점에 Floor 4장(2x2)과 Player Spawn Pad 1개 생성.
- 입력은 (Forward, Left, Up) 순서의 월드 좌표이며 원점 오프셋은 없다.
- 지정 좌표는 바닥 묶음 중앙의 윗면과 Spawn Pad의 원점 기준이다.
- Floor 크기는 원본을 유지한다. 원본의 월드 바운드로 타일 간격을 계산한다.
  장식 때문에 바운드가 실제 타일 간격과 다르면 FLOOR_TILE_SIZE_FL을 지정한다.
- 원본 2개는 보존한다. 별도로 맵 밖에 옮기거나 결과 확인 후 직접 제거한다.
  원본 Spawn Pad도 활성 스폰 장치이므로 플레이 테스트 전 제외해야 한다.
- 같은 결과 이름이 이미 있으면 생성 전 중단한다. 기존 맵은 덮어쓰지 않는다.
- 자동 저장하지 않는다. 생성 확인 후 사용자가 저장한다.

좌표 변환: unreal.Vector(Forward, -Left, Up)
Python API의 XYZ와 UEFN 표시 좌표는 다르므로 (X, Z, Y) 순서 교환만 하지 않는다.
E, F의 생략된 Up은 0으로 가정했다. 아래 SPAWN_POINTS_FLU에서 변경할 수 있다.

참고
https://dev.epicgames.com/documentation/fortnite/python-tools-in-uefn
https://dev.epicgames.com/documentation/fortnite/leftupforward-coordinate-system-in-unreal-editor-for-fortnite
https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorActorSubsystem

이 파일은 에디터 배치용이다. 장치 복제·설정 유지·충돌·스폰 동작은 UEFN에서
실제 검증해야 한다. 경기 시작·개인전·최대 인원 설정까지 변경하지는 않는다.
"""

import unreal


FLOOR_TEMPLATE_LABEL = 'GOUP_Floor_Template'
SPAWN_TEMPLATE_LABEL = 'GOUP_PlayerSpawn_Template'
OUTPUT_PREFIX = 'GOUP_Start'

# None: 원본 Floor의 월드 바운드를 사용한다.
# 필요하면 한 장의 실제 간격을 (Forward 길이, Left 길이)로 지정한다.
# 예: FLOOR_TILE_SIZE_FL = (512.0, 512.0)
FLOOR_TILE_SIZE_FL = None

# Spawn Pad 원점은 입력한 좌표 그대로 둔다. 띄워야 하면 Up 방향 보정값 지정.
SPAWN_UP_OFFSET = 0.0

SPAWN_POINTS_FLU = {
    'A': (6144.0, 0.0, 0.0),
    'B': (5120.0, -4096.0, 0.0),
    'C': (1024.0, -6144.0, 0.0),
    'D': (-3072.0, -5632.0, 0.0),
    'E': (-6144.0, -2048.0, 0.0),
    'F': (-6144.0, 2048.0, 0.0),
    'G': (-3072.0, 5632.0, 0.0),
    'H': (1024.0, 6144.0, 0.0),
    'I': (5120.0, 4096.0, 0.0),
}


def flu_to_xyz(forward, left, up):
    """FLU로 입력한 월드 좌표를 Unreal Python API의 XYZ로 변환한다."""
    return unreal.Vector(forward, -left, up)


def require_template(actors, label):
    matches = [actor for actor in actors if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(
            f"Outliner에 '{label}' 원본이 정확히 1개 필요합니다. 현재 {len(matches)}개."
        )
    return matches[0]


def place_actor(actor, location):
    if not actor.set_actor_location(location, False, True):
        raise RuntimeError(f'{actor.get_actor_label()} 위치 설정 실패')


def create_start_platforms():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = subsystem.get_all_level_actors()
    floor_template = require_template(actors, FLOOR_TEMPLATE_LABEL)
    spawn_template = require_template(actors, SPAWN_TEMPLATE_LABEL)

    rotation = floor_template.get_actor_rotation()
    angles = (rotation.pitch, rotation.yaw, rotation.roll)
    if any(abs((angle + 180.0) % 360.0 - 180.0) > 0.01 for angle in angles):
        raise RuntimeError('Floor 원본의 Pitch/Yaw/Roll을 모두 0으로 맞춰 주세요.')

    _, extent = floor_template.get_actor_bounds(False)
    tile_forward, tile_left = (
        FLOOR_TILE_SIZE_FL if FLOOR_TILE_SIZE_FL is not None
        else (extent.x * 2.0, extent.y * 2.0)
    )
    if tile_forward <= 0.0 or tile_left <= 0.0:
        raise RuntimeError('Floor 한 장의 가로·세로 간격이 0보다 커야 합니다.')

    # 생성하려는 이름만 검사한다. 사용자 소유의 다른 액터는 변경하지 않는다.
    expected_labels = set()
    for point in SPAWN_POINTS_FLU:
        expected_labels.add(f'{OUTPUT_PREFIX}_{point}_PlayerSpawn')
        for index in range(1, 5):
            expected_labels.add(f'{OUTPUT_PREFIX}_{point}_Floor_{index}')
    conflicts = sorted({a.get_actor_label() for a in actors} & expected_labels)
    if conflicts:
        raise RuntimeError('이미 생성된 이름이 있어 중단합니다: ' + ', '.join(conflicts))

    created = []
    with unreal.ScopedEditorTransaction('GO UP - Create 9 Start Platforms'):
        try:
            for point, (forward, left, up) in SPAWN_POINTS_FLU.items():
                index = 0
                for offset_forward in (-tile_forward / 2.0, tile_forward / 2.0):
                    for offset_left in (-tile_left / 2.0, tile_left / 2.0):
                        index += 1
                        floor = subsystem.duplicate_actor(floor_template)
                        if floor is None:
                            raise RuntimeError(f'{point}: Floor 복제 실패')
                        created.append(floor)
                        floor.set_actor_label(f'{OUTPUT_PREFIX}_{point}_Floor_{index}')

                        target = flu_to_xyz(
                            forward + offset_forward, left + offset_left, up
                        )
                        # 피벗 위치가 중앙이 아닌 Floor도 바운드 중앙·윗면으로 맞춘다.
                        center, bounds = floor.get_actor_bounds(False)
                        pivot = floor.get_actor_location()
                        place_actor(floor, unreal.Vector(
                            pivot.x + target.x - center.x,
                            pivot.y + target.y - center.y,
                            pivot.z + target.z - (center.z + bounds.z),
                        ))

                spawn = subsystem.duplicate_actor(spawn_template)
                if spawn is None:
                    raise RuntimeError(f'{point}: Player Spawn 복제 실패')
                created.append(spawn)
                spawn.set_actor_label(f'{OUTPUT_PREFIX}_{point}_PlayerSpawn')
                place_actor(spawn, flu_to_xyz(forward, left, up + SPAWN_UP_OFFSET))
                unreal.log(f'[GO UP] {point}: FLU=({forward}, {left}, {up})')
        except Exception:
            # 이번 실행에서 만든 액터만 되돌리고 원래 오류를 유지한다.
            for actor in reversed(created):
                try:
                    subsystem.destroy_actor(actor)
                except Exception as cleanup_error:
                    unreal.log_warning(f'[GO UP] 생성 액터 정리 실패: {cleanup_error}')
            raise

    subsystem.set_selected_level_actors(created)
    unreal.log(
        f'[GO UP] 완료: Spawn {len(SPAWN_POINTS_FLU)}개, '
        f'Floor {len(SPAWN_POINTS_FLU) * 4}장. '
        f'묶음 크기 FL=({tile_forward * 2.0}, {tile_left * 2.0}). '
        '원본 Spawn Pad를 플레이에서 제외하고 결과를 확인한 뒤 저장하세요.'
    )


if __name__ == '__main__':
    create_start_platforms()
