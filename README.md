# KYVIKOS — preVue Digital Twin

주식회사 큐비크스 홈페이지 프로토타입. 실제 수행한 전시·행사 공간을 3D로 재구성하고,
**와이어프레임 ↔ 실제 구현** 전환과 **시점 이동**으로 preVue(디지털 트윈) 역량을 보여줍니다.

## 수록된 공간

| 공간 | 주소 |
| --- | --- |
| APEC CEO Summit 특별만찬 (경주 황룡원) | `#apec` |
| 현대자동차 1억대 생산기념 전시 (현대 모터스튜디오 도산) | `#hyundai` |
| 장미셸 바스키아 SEOUL 전시 (DDP) | `#basquiat` |
| LOCAL POWER 2025 홍콩 패션 in 서울 (성수 세원정밀 창고) | `#localpower` |

## 실행

```bash
npm install
npm run dev     # http://localhost:5173
npm run build   # dist/ 생성
```

## 구조

```
src/
  main.js              렌더러, 카메라 이동, 모드 전환, UI
  scene/kit.js         Builder(지오메트리 병합), 재질, 트러스·지붕 등 공용 부품
  scene/environment.js 하늘돔, 별
  venues/registry.js   공간 목록
  venues/<id>/         공간별 모델링(scene.js) · 시점과 문구(data.js) · 텍스처
public/images/<id>/    시점 카드 이미지 (sim-* 3D 렌더 / real-* 실제 사진)
```

공간 모듈 작성 규약은 [src/venues/README.md](src/venues/README.md) 참고.

## 실사 에셋

텍스처·3D 모델·HDRI는 [Poly Haven](https://polyhaven.com)의 CC0(퍼블릭 도메인) 에셋입니다.
`npm run assets` 로 다시 받아 최적화할 수 있습니다 (원본은 `assets-src/`, 결과물은 `public/assets/`).

## 참고

- 3D 모델은 원본 3D 파일 없이 **사진과 렌더를 보고 재구성한 근사 모델**입니다. 치수는 실측이 아닙니다.
- 시점 설명 문구는 임시 문안이며, 실제 내용에 맞게 수정이 필요합니다.
- 전시 그래픽·사이니지는 분위기만 재현한 것으로, 실제 작품이나 브랜드 로고는 사용하지 않았습니다.
