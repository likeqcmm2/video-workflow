# Style profile
test

## HOOK
#### S001
NAR: 1986年1月28日、フロリダの空に白い煙が伸びました。
VIS: CLIP @1.0 | stamp=1986年1月28日　フロリダ州
#### S002 | pause=1.0
NAR: なぜ止められなかったのでしょうか。今回は、その真相を見ていきます。
VIS: img:assets/img/landscape.jpg | credit=写真：テスト | kb=in
VIS: gfx:quote | text=「あれは爆発する」 | attr=技術者

## BODY
### CH1 | 第1章 | 小さなゴムの輪
#### S101
NAR: NASAは、年間24回の打ち上げを目標にしていました。
VIS: gfx:bars | spec=flights | step=2
#### S102
NAR: 損傷は何度も見つかっていました。
VIS: gfx:timeline | spec=events
#### S103
NAR: 低温ほど損傷が起きていたのです。担当者はこう語っています。
VIS: gfx:scatter | spec=pts
VIS: img:assets/img/portrait.jpg | credit=写真：テスト | lt=ロジャー・ボイジョリー／サイオコール社の技術者
#### S104
NAR: この部品こそが、問題の中心でした。
VIS: gfx:ring | title=接合部の模式図
#### S105
NAR: シャトルは三つの州を結ぶ会議で判断されました。
VIS: gfx:map | region=us48 | highlight=Utah;Alabama;Florida | points=ut|-112.2|41.6|ユタ州|サイオコール社|30|-20;al|-86.6|34.6|アラバマ州|マーシャル宇宙飛行センター|40|-95;fl|-80.6|28.5|フロリダ州|ケネディ宇宙センター|40|30 | links=ut-al;al-fl;ut-fl | caption=3か所を結んだ電話会議
### CH2 | 第2章 | 73秒
#### S201
NAR: 当日の気温は、華氏36度でした。
VIS: gfx:gauge | min=-20 | max=30 | tick=10 | unit=℃ | value=2.2 | label=打ち上げ時の気温　約2℃ | sub=それまでで最も寒い | color=accent | ref=11.7|これまでの最低
#### S202
NAR: 映像は、少しずつ暗くなっていきました。
VIS: CLIP @10.0
#### S203
NAR: 報告書は、九つの改善を勧告しました。
VIS: gfx:list | title=委員会の勧告 | items=設計の見直し;管理体制の見直し;安全監督部門の設置 | highlight=3 | numbering=roman
VIS: gfx:document | lines=MORTON THIOKOL, INC.\N\N31 July 1985\N\NSUBJECT: O-Ring Erosion | caption=技術者のメモ | sub=1985年7月31日 ／ 文面の一部を再現 | highlight=5-5

Length check: hook 64 chars (sample 60), body 165, total 229 — PASS (2026-10-21 06:07)
