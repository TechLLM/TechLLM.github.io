---
title: "Obsidian 노트 앱이 해킹 경로로? PHANTOMPULSE RAT 공격 완전 분석"
date: 2026-05-12T09:44:00+09:00
draft: false
description: "금융·암호화폐 전문가를 노린 REF6598 캠페인은 Obsidian 공유 볼트와 커뮤니티 플러그인을 미끼로 PHANTOMPULSE RAT을 심는다. 이더리움 블록체인으로 C2 주소를 숨기는 정교한 수법을 분석한다."
cover:
  image: "/images/obsidian-phantompulse-rat-cover.jpg"
  alt: "Obsidian 볼트를 통해 침투하는 PHANTOMPULSE RAT 해킹 공격 일러스트"
  caption: ""
tags: ["보안", "악성코드", "Obsidian", "RAT", "소셜엔지니어링", "암호화폐"]
categories: ["Security"]
---

## 핵심 요약

- **REF6598 캠페인**은 Obsidian 공유 볼트를 무기화해 금융·암호화폐 종사자를 표적으로 삼는다.
- 공격자는 LinkedIn·Telegram에서 벤처캐피털리스트를 사칭해 신뢰를 쌓은 뒤 악성 볼트 초대를 보낸다.
- 피해자가 커뮤니티 플러그인 동기화를 허용하는 순간, 변조된 'Shell Commands' 플러그인이 실행된다.
- Windows에서는 PowerShell → PHANTOMPULL 로더 → PHANTOMPULSE RAT 순으로 메모리에 직접 주입된다.
- PHANTOMPULSE는 **이더리움 블록체인 트랜잭션**에 C2 서버 IP를 숨겨, 차단이 극도로 어렵다.

## 신뢰를 이용하는 공격 시나리오

공격은 LinkedIn이나 Telegram에서 시작된다. 위협 행위자(REF6598)는 벤처캐피털리스트나 업계 관계자로 위장해 금융·암호화폐 전문가에게 접근한다. 충분한 신뢰가 쌓이면 "함께 자료를 공유하자"며 클라우드에 호스팅된 **Obsidian 공유 볼트** 링크를 보낸다.

볼트를 열면 Obsidian이 "커뮤니티 플러그인 동기화"를 활성화하라는 프롬프트를 표시한다. 이 설정은 사용자가 직접 승인해야 하는 단계지만, 공격자는 이를 사전에 정교하게 사회공학적으로 유도한다. 승인 즉시 볼트에 내장된 악성 버전의 **'Shell Commands'** 및 **'Hider'** 플러그인이 활성화된다.

## 공격 체인: Windows와 macOS 모두 타깃

플랫폼별로 세부 흐름은 다르지만 구조는 같다.

**Windows 공격 흐름**
1. Shell Commands 플러그인이 `powershell -ExecutionPolicy Bypass` 명령을 실행
2. PowerShell 스크립트가 **PHANTOMPULL** 로더를 드롭
3. PHANTOMPULL이 최종 페이로드 **PHANTOMPULSE RAT**을 복호화해 메모리에 직접 인젝션 (파일 기반 탐지 우회)

**macOS**는 AppleScript를 통해 동일한 구조의 로더가 실행된다.

## 블록체인을 C2 은신처로 활용하는 PHANTOMPULSE

PHANTOMPULSE의 가장 주목할 특징은 **이더리움 블록체인을 C2 통신 채널**로 쓴다는 점이다. 악성코드는 하드코딩된 지갑 주소의 최신 트랜잭션을 조회하고, 그 데이터 안에 삽입된 C2 서버 IP를 추출한다. 블록체인 트랜잭션은 분산화·불변성이 특성이라 특정 도메인이나 IP를 차단하는 전통적 방어 방식이 통하지 않는다.

RAT이 설치되면 공격자는 **키로깅·스크린샷 캡처·파일 탈취·임의 명령 실행**이 가능해진다. 금융·암호화폐 분야 피해자의 경우 거래소 자격증명이나 암호화폐 지갑 키까지 빼앗길 수 있다.

## 실무자가 볼 핵심 포인트

| 구분 | 권고 사항 |
|------|-----------|
| **EDR 규칙** | Obsidian.exe가 powershell.exe·cmd.exe·osascript를 자식 프로세스로 생성하면 즉시 알럿 |
| **네트워크 모니터링** | 일반 엔드포인트에서 이더리움 노드·게이트웨이로 나가는 아웃바운드 연결 탐지 |
| **플러그인 정책** | 공식 Obsidian 마켓플레이스 외 커뮤니티 플러그인 설치·실행 차단 |
| **볼트 공유 주의** | 출처 불명의 공유 볼트에서 플러그인 동기화 절대 활성화 금지 |
| **사용자 교육** | 금융·암호화폐 직군 대상 협업 도구 소셜엔지니어링 위협 인식 교육 실시 |

*원문: [Obsidian Plugin Abused in Social Engineering Campaign to Deliver New PHANTOMPULSE RAT](https://cyber.netsecops.io/articles/obsidian-plugin-abused-in-campaign-to-deploy-phantom-pulse-rat/) — Jason Gomes, CyberNetSec.io*
