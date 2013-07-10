;------------------------------------------------------------
address 0x000
boot:
  call init
loop:
  jump loop

;------------------------------------------------------------
;D:/Work/Checkout.Git/picoblaze_utils/test.c
init:
 L_f512cca69f269d9d7abd0a0f2e96a5f4_0:
 ;D:/Work/Checkout.Git/picoblaze_utils/test.c:12
  ;void init (void)

 L_f512cca69f269d9d7abd0a0f2e96a5f4_1:
 ;D:/Work/Checkout.Git/picoblaze_utils/test.c:14
    ;while (s0 == s0), L_f512cca69f269d9d7abd0a0f2e96a5f4_2, JOIN_0
    compare s0, s0
    jump NZ, JOIN_0

 L_f512cca69f269d9d7abd0a0f2e96a5f4_2:
 ;D:/Work/Checkout.Git/picoblaze_utils/test.c:15
        move s0, s0

 JOIN_2:
 ;D:/Work/Checkout.Git/picoblaze_utils/test.c:14
    ;endwhile
    jump L_f512cca69f269d9d7abd0a0f2e96a5f4_1

 JOIN_0:
 ;D:/Work/Checkout.Git/picoblaze_utils/test.c:12
  ;endfunc

_end_init:
  return


;------------------------------------------------------------
;D:/Work/Checkout.Git/picoblaze_utils/test.c
isr_test:
 L_f512cca69f269d9d7abd0a0f2e96a5f4_3:
 ;D:/Work/Checkout.Git/picoblaze_utils/test.c:5
  ;bool_t isr_test (void)

 L_f512cca69f269d9d7abd0a0f2e96a5f4_4:
 ;D:/Work/Checkout.Git/picoblaze_utils/test.c:7
    move s0, 0
 ;D:/Work/Checkout.Git/picoblaze_utils/test.c:8
    output s0, 255
 ;D:/Work/Checkout.Git/picoblaze_utils/test.c:9
    returni enable

 JOIN_1:
 ;D:/Work/Checkout.Git/picoblaze_utils/test.c:5
  ;endfunc

_end_isr_test:
  returni enable



;ISR
address 0x3F0
jump    isr_test
