//basetype
typedef unsigned char uint8_t;
typedef uint8_t bool_t;
#define true    1
#define false   0

//internal instruction
//I/O
extern void input(uint8_t addr, uint8_t* reg);
extern void output(uint8_t addr, uint8_t* reg);

extern void fetch(uint8_t addr, uint8_t* reg);
extern void store(uint8_t addr, uint8_t* reg);

//interrupt
extern void enable_interrupt();
extern void disable_interrupt();

//format: psm("addcy %1, 0", &idx_cycle_h);
//format: psm("xor %1, %2", &idx_cycle_h, &idx_cycle_l);
extern void psm(char* fmt, ...);

//registers
extern uint8_t s0;
extern uint8_t s1;
extern uint8_t s2;
extern uint8_t s3;
extern uint8_t s4;
extern uint8_t s5;
extern uint8_t s6;
extern uint8_t s7;
extern uint8_t s8;
extern uint8_t s9;
extern uint8_t sA;
extern uint8_t sB;
extern uint8_t sC;
extern uint8_t sD;
extern uint8_t sE;
extern uint8_t sF;

