# Style profile
test

## HOOK
#### S001
NAR: 1986年1月28日、フロリダの空に白い煙が伸びました。
VIS: CLIP @1.0 | stamp=1986年1月28日　フロリダ州 | overlay=gfx:label | label=打ち上げの瞬間
#### S002 | pause=1.0
NAR: なぜ止められなかったのでしょうか。今回は、その真相を見ていきます。
VIS: img:assets/img/landscape.jpg | credit=写真：テスト | kb=in
VIS: gfx:quote | text=「あれは爆発する」 | attr=技術者 | in=dissolve:0.6

## BODY
### CH1 | 第1章 | 小さなゴムの輪
#### S101
NAR: NASAは、年間24回の打ち上げを目標にしていました。
VIS: gfx:bars | spec=flights
#### S102
NAR: その仕組みは、こうした動きで説明できます。
VIS: anim:assets/anim/cells.mp4 @0:02.0
#### S103
NAR: 低温ほど損傷が起きていたのです。担当者はこう語っています。
VIS: gfx:document
VIS: img:assets/img/portrait.jpg | credit=写真：テスト | lt=ロジャー・ボイジョリー／サイオコール社の技術者 | in=dissolve:0.5
#### S105
NAR: シャトルは三つの州を結ぶ会議で判断されました。
VIS: gfx:map
### CH2 | 第2章 | 73秒 | grade=archive
#### S201 | subs=off
NAR: 「あれは爆発する」。
VIS: gfx:quote | text=「あれは爆発する」 | attr=ボブ・イーベリング
#### S202
NAR: 映像は、少しずつ暗くなっていきました。
VIS: CLIP @10.0 | overlay=anim:assets/anim/line_alpha.webm | out=fade:0.8
#### S203
NAR: 報告書は、九つの改善を勧告しました。
VIS: img:assets/img/small.jpg | credit=写真：テスト | fit=contain | grade=main | in=fade:0.4

Length check: hook 64 chars (sample 60), body 146, total 210 — PASS (2026-10-21 07:34)
