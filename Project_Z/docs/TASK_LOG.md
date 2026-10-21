# Project_Z 작업 기록

## 2026-10-22 — 팀 HUD·팀 마커 PIE 검증

- `WBP_TeamStatus`를 `WBP_FPS_HUD`의 `TeamStatus` 자식으로 배치하고 C++ `BindWidgetOptional` 연결 확인.
- 최초 미표시 원인은 `BP_Project_Z_MultiPlayerController`의 `HUDWidgetClass`가 `WBP_TPS_HUD`를 가리키던 설정 오류였음.
- `HUDWidgetClass`를 `WBP_FPS_HUD`로 변경한 뒤 상단 `TEAM A / TEAM B` 상태 HUD 표시 확인.
- `WBP_PlayerTeamMarker`를 만들고 `BP_ZCharacter_FPS`의 `Team Marker Widget Class`에 연결.
- 원격 플레이어의 `TEAM A`/`TEAM B` 마커 표시 및 팀 정보 갱신 확인.
- 장애물 뒤에서 마커가 숨고 시야가 확보되면 다시 표시되는 동작까지 PIE 검증 완료.
- 아직 완료로 판정하지 않음: 적 처치 점수 양쪽 동기화, 아군 처치 점수 제외, 사망·리스폰 후 팀·HUD·마커·점수 유지.
- 다음 작업 인계 문서: [2026-10-22 다음 작업 컨텍스트](2026-10-22_Project_Z_다음작업_컨텍스트.md).

## 2026-10-21 — 팀 HUD·아군/적군 마커·팀 스코어

- 로컬 전투 HUD 상단에 확정 팀과 A/B 점수 표시 추가.
- 원격 플레이어 머리 위에 절대 소속 기준 `TEAM A`/`TEAM B` 마커 추가.
- 팀 상태·마커 C++ 클래스를 WBP 부모로 사용할 수 있도록 BindWidgetOptional 및 클래스 선택 프로퍼티 추가.
- 팀 상태 위젯을 `WBP_FPS_HUD`의 `TeamStatus` 자식으로 직접 바인딩하고 별도 Viewport 생성 코드를 제거.
- 카메라와 대상 사이 WorldStatic/WorldDynamic 차폐 검사로 벽 뒤 마커 숨김 처리 추가.
- 적 팀 처치 시 서버 GameState 팀 점수 증가 및 복제 연결.
- 아군 처치는 점수에서 제외하며 아군 피해 차단은 아직 적용하지 않음.
- UHT, Project_ZEditor Win64 Development 컴파일 및 링크 성공. 팀 HUD·마커·벽 가림 PIE 검증 완료, 점수·리스폰 연계 검증은 남음.
- 상세 문서: [팀 HUD·마커·스코어 구현 기록](2026-10-21_Project_Z_팀HUD_마커_스코어.md).

## 2026-10-21 — 팀 선택 검증 현황 및 일정 대조

- 추가 문서: [팀 선택 검증현황 및 다음 일정](2026-10-21_Project_Z_팀선택_검증현황_및_다음일정.md).
- 코드 기준: 원격 `c60a20f`. 팀 선택·결과·재시도 RPC와 UI 연결 구현 확인.
- 사용자 확인: 스폰, B팀 선택/서버 저장, 시작점 충돌 제외, 실패 시 재시도 버튼, 재시도 실패 로그.
- 보류: 장애물 제거 후 재시도 성공 테스트. 양쪽 팀별 최초 스폰·리스폰 종합 검증은 남음.
- 잔여 코드 항목: 재시도 GameMode 실패 분기의 return 누락, 최초 요청의 GameMode 검사 누락, 스폰 실패 시 SpawnBlocker 삭제 테스트 코드.
- 다음 주요 기능: PlayerState 기반 내 HUD 팀 표시 → 다른 플레이어 팀 식별 → 팀별 리스폰 확인.
- 소스·에셋 수정 및 빌드·PIE 실행 없음. 문서만 변경.

## 2026-10-20 — 팀 선택 UI 진행 기록

- 대상: Project_Z, WorkSpace 저장소.
- 추가 문서: [팀 선택 UI 진행현황](2026-10-20_Project_Z_팀선택_UI_진행현황.md).
- 내용: C++ UI 동작/BP 배치 분담, 임시 선택 후 입장 확정, Widget 및 Controller 작업, 시작점 초기화 오류 대응, 남은 RPC 구현.
- 검증: 업로드 중 추가된 원격 `e8fda3b`까지 확인. UI 표시는 사용자 확인. 코드상 PlayerState 검사 반전, B팀 색상 대상 오류, 준비 검사 미연결 등을 기록. 빌드·PIE 미실행.
- 소스 및 에셋 변경 없음.
- 다음 작업: 기록된 코드 오류 수정 → 준비 검사 및 버튼 동작 확인 → 서버 요청/결과/재시도 연결.
