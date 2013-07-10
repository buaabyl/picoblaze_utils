picoblaze_utils
===============

picoblaze c-compiler and assembly and linker writing in python.


This is easy assembly like c style, not really c!

You can use macro, this python depend on mcpp(preprocessor) and astyle(style formater).

mcpp: http://mcpp.sourceforge.net/

astyle: http://astyle.sourceforge.net/


```c
#define r_io s0
bool_t isr_test(void) __attribute__((interrupt ("IRQ0")));

bool_t isr_test(void)
{
    r_io = 0x00;
    output(0xFF, &r_io);
    return true;
}

void init(void)
{
    while (s0 == s0) {
        s0 = s0;
    }
}
```

I am still learning llvm, so this tools maybe rewrite to llvm later.
