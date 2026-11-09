#include <stdio.h>
volatile int health = 100;
volatile int score = 100;
void take_damage(int amount) { if (amount > 0) health -= amount; }
int main(void) { take_damage(7); printf("%d %d\n",health,score); return 0; }
