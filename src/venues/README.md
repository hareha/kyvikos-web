# 공간(venue) 모듈 규약

`src/venues/<id>/index.js` 는 아래 4가지를 export 합니다. 예시는 `apec/`.

```js
export const project = {
  eyebrow: 'PORTFOLIO · 2025',
  title: '줄1 <br />줄2',          // HTML 허용 (<br /> 앞에 공백)
  meta: [['클라이언트', '...'], ['장소', '...'], ['과제', '...'], ['수행 범위', '...']],
  tech: '<b>preVue</b>로 ...',     // HTML 허용
};

export const env = {
  height: 20,      // 가장 높은 오브젝트 높이(m) + 여유. 전환 스캔이 이 높이까지 올라감
  sky: null,       // 실외면 { zenith, horizon, moon: [x,y,z] }, 실내면 null
  stars: false,    // 실외 밤이면 true
  builtBg: '#0a0c12', // sky가 null일 때 실제 구현 모드 배경색
  fog: 0.004,      // 실제 구현 모드 안개 밀도
  exposure: 1,     // 톤매핑 노출
};

// 첫 번째는 반드시 id: 'overview'
export const views = [
  { id: 'overview', label: '전체 조감', pos: [x,y,z], target: [x,y,z], fov: 45, orbit: true },
  {
    id: 'stage', label: '무대 위',
    pos: [...], target: [...], fov: 60,
    orbit: false,              // true: 대상 주위 회전 / false: 제자리 둘러보기(1인칭)
    anchor: [x, y, z],         // 3D 핀 위치
    sim: 'sim-xxx',            // public/images/<id>/sim-xxx.jpg (3D 렌더)
    real: 'real-xxx',          // public/images/<id>/real-xxx.jpg (실제 사진)
    desc: '한두 문장 설명',
  },
];

export function build() {
  // Builder로 모델링 → { root: THREE.Group, lights: [{ light, base }] }
  // lights 의 intensity 는 main.js 가 base × (실제 구현 진행도)로 매 프레임 설정
}
```

## 모델링 규칙
- 단위 m, 공간 중심이 원점, y가 위.
- `scene/kit.js`의 `Builder`로 추가 → 재질별 병합. 개별 `THREE.Mesh`를 대량으로 만들지 말 것.
- 모든 솔리드 재질은 `std()` / `glow()` / `revealable()` 로 만들 것 (전환 효과).
- 선 레이어: 큐비크스가 만든 것(무대·전시물·구조물)은 `event`(밝게), 원래 건물·지형은 `context`(흐리게).
- 작은 소품·곡면이 많은 것은 `{ outline: false }` 로 선을 줄여 와이어프레임을 깔끔하게.
- 조명은 `lights` 로 반환해야 모드 전환에 따라 켜지고 꺼짐.
