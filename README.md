# Type Korean CJJ

# 개요
Glyphs 3의 편집창(텍스트 툴)에서 한글 자모를 **초성·중성·종성 글리프로 바로 입력**할 수 있게 해주는 타이핑 모드입니다.
<br>
평소 키보드로 한글을 치면 호환 자모(`kiyeokCompa-ko`)가 들어가거나 음절로 조합되어, 초성 `kiyeokCho-ko` · 중성 `aJung-ko` · 종성 `kiyeokJong-ko` 같은 글리프를 늘어놓고 작업하려면 하나씩 찾아 넣어야 했습니다. 이 플러그인을 켜면 두벌식 자판 그대로 위치형 자모 글리프가 입력됩니다.
<br>
<br>

## 기능
- **Edit → 한글 초·중·종성 입력 (⌃R)**: 누를 때마다 모드가 바뀝니다.
  **꺼짐(기본 타이핑) → 초성 모드 → 종성 모드 → 꺼짐 …**
- 초성 모드에서는 자음이 초성, 종성 모드에서는 자음이 종성으로 들어가고, 모음은 항상 중성으로 입력됩니다.
- Shift로 쌍자음(ㄲ ㄸ ㅃ ㅆ ㅉ)과 ㅒ ㅖ를 입력합니다.
- 겹모음·겹받침은 **0.4초 안에 연달아 치면** 합쳐집니다. (예: ㅗ+ㅏ → ㅘ, 종성 모드에서 ㄹ+ㄱ → ㄺ) 천천히 치면 따로 들어갑니다.
- 입력 소스가 한글이든 영문이든 키 위치(두벌식) 기준으로 동작합니다.
- 폰트에 해당 글리프가 없거나 종성에 없는 자모(ㄸ ㅃ ㅉ)를 치면 경고음만 나고 아무것도 입력되지 않습니다.
- 단축키는 Glyphs 설정 → Shortcuts에서 바꿀 수 있습니다.
<br>

## 설치
- `TypeKoreanCJJ.glyphsPlugin`을 더블클릭해 설치한 뒤 Glyphs를 재시작합니다.
- **Glyphs 3 전용**입니다. Glyphs 4 지원은 호환성 확인 후 추가할 예정입니다.
<br>

## 사용
1. 편집창에서 텍스트 툴(T)을 선택합니다.
2. ⌃R로 초성 모드를 켭니다. (알림과 Edit 메뉴 항목 이름으로 현재 모드가 표시됩니다)
3. 자모를 칩니다. 자음을 종성으로 넣고 싶으면 ⌃R을 한 번 더 누릅니다.
4. 한 번 더 누르면 원래 입력으로 돌아갑니다.

⌘·⌃·⌥ 조합 키, 방향키, 스페이스, 리턴, 삭제 등은 그대로 동작합니다. 편집창이 아닌 곳(Font Info 등의 입력란)에서는 키 입력을 가로채지 않습니다.

문제가 생기면 **Window → Macro Panel** 아래쪽 출력 영역에 `TypeKoreanCJJ:`로 시작하는 메시지가 표시됩니다.
<br>
<br>

# English
A typing mode for the Glyphs 3 Edit View (Text tool) that inserts **positional Hangul jamo glyphs** — Choseong (`kiyeokCho-ko`), Jungseong (`aJung-ko`) and Jongseong (`kiyeokJong-ko`) — instead of compatibility jamo, using the Dubeolsik key layout regardless of the active input source.

- **Edit → Type Hangul Jamo (⌃R)** cycles Off (normal typing) → Choseong → Jongseong → Off. Consonants follow the mode; vowels always insert Jungseong.
- Shift gives tense consonants and ㅒ ㅖ; compound vowels and finals combine when the second key follows within 0.4 s (ㅗ+ㅏ → ㅘ, ㄹ+ㄱ → ㄺ).
- Messages go to Window → Macro Panel.
- Glyphs 3 only for now.

## Development
The key mapping and combining logic lives in `Contents/Resources/jamo_logic.py` (no Glyphs dependency) and is tested with:

```
python3 -m unittest discover -s tests
```
