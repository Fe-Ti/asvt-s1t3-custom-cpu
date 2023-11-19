; R0 is mask
; R5 is odd ctr
; R6 is even ctr

begin:		set r1 0xf
			set r0 0x0
			ind0 r0
			ind1 r0
			ind2 r0
			ind3 r0
			indctrl r1
			input r1 ; low part
			ind3 r1
			input r2 ; high part
			ind2 r2
			set r6 0x0 ; set counter `even` to zero
			set r5 0x0 ; set counter `odd` to zero
			set r0 0x8 ; mask

chk_odd:	mov r3 r2
			and r3 r0
			jz shift_num1
			inc r5
shift_num1:	dshl r2 r1 ; shift high part with bit from low (HHHH -> HHHL)
			shl r1 ; shift low part (LLLL -> LLL0)

chk_eve:	mov r3 r2 ; copy r2 to r3
			and r3 r0 ; check r3 highest bit
			jz shift_num2
			inc r6
shift_num2:	dshl r2 r1 ; shift high part with bit from low (HHHH -> HHHL)
			shl r1 ; shift low part (LLLL -> LLL0)
			mov r7 r2
			or r7 r1 ; if 0 then there is nothing to count
			jnz chk_odd
			
			ind2 r5
			ind3 r6
			mov r1 r5 ; in case if r5 < r6 there will be a backup
			sub r5 r6 ; if C4 => sub is correct
			jc4 chk_diff
			sub r6 r1
			mov r5 r6
chk_diff:	set r0 0x0 ; here is hardcoded check for 0 or 3
			set r3 0x3 ; for larger scale it should be recursive thing
			ind2 r0 ; clear screen just because we have r0 == 0 :-)
			ind3 r0
			ind3 r5
			sub r5 r0
			jz prt_yes
			sub r5 r3
			jz prt_yes
prt_no:		set r0 0xb
			indctrl r0
			set r1 0x1
			ind0 r1
			set r2 0x7
			ind1 r2
			set r3 0x0
			ind3 r3
			jmp check_inp
prt_yes:	set r0 0xe
			indctrl r0
			set r1 0xc
			ind1 r1
			set r2 0xd
			ind2 r2
			set r3 0x5
			ind3 r3
check_inp:	chkin ; wait for user input
			jz check_inp
			jmp	begin
