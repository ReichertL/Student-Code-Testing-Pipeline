#include <stdio.h>
#include <string.h>
#include <stdbool.h> 
#include <stdlib.h>
#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <inttypes.h>

int64_t  current_size;
int64_t  num_blocks;

struct candidate{
	int64_t  ux;//up or left
    int64_t uy;
    int64_t dx;//down or right
    int64_t  dy;

};
struct candidate * create_can(int64_t  ux, int64_t  uy, int64_t dx, int64_t dy){
    struct candidate *c= malloc(sizeof(int64_t ) * 4); 
    c->ux=ux;
    c->uy=uy;
    c->dx=dx;
    c->dy=dy;
    return c;
}

int64_t counting_up(int64_t i){
    
    if(i==0){
        i=1;
    }else if(i%2 ==0){
        i=i-2;
    }else{
        //uneven
        i=i+2;
    }
    return i;
    
}

int64_t counting_down(int64_t i){
    if(i==1){
        i=0;
    }else if(i==0){
        i=2;
    }else if(i%2 ==0){
        i=i+2;
    }else{
        //uneven
        i=i-2;
    }
    return i;
        
}

bool check_in_list(int64_t ** list , int64_t len, int64_t x, int64_t y){
    
    for(int64_t i=0; i<len;i++){
        int64_t * block=list[i];
        if(block[0]==x && block[1]==y){
            return true;
        }
    }
    return false;
    
}

bool check_in_candidates(struct candidate **candidates, struct candidate *c, int64_t cc){
    for(int64_t i=0;i<cc;i++){
        struct candidate *d =candidates[i];
        if(d->ux==c->ux && d->uy==c->uy && d->dx==c->dx && d->dy ==c->dy){
            return true;
        }
    }
    return false;
}

void print_game_status(short ** game_xaxis, int64_t * top_yvalue){
    int64_t start;
    int64_t max_start=current_size-1;
    if(max_start%2==0){
        start=max_start;
    }else{
        start=max_start-1;
    }
    
    for(int64_t x=start; x>0; x=x-2){
        printf("-%" PRId64 ":",(x)/2);
        if( top_yvalue[x]>0){
            short* collumn=game_xaxis[x];
            for(int64_t i=0; i<top_yvalue[x];i++){
                printf("%d"  , collumn[i]-1);
            }
        }

        printf("\n");        
    }

    int x=0;
    short* collumn=game_xaxis[x];
    printf(" 0:");
    for(int64_t i=0; i<top_yvalue[x];i++){
        printf("%d ", collumn[i]-1);
    }
    printf("\n");
    
    for(int64_t x=1; x<=current_size; x=x+2){
        printf(" %" PRId64 ":",(x)/2+1);
        short* collumn=game_xaxis[x];
        for(int64_t i=0; i<top_yvalue[x];i++){
            printf("%d ", collumn[i]-1);
        }

        printf("\n");        
    }

}

void print_all_blocks(short ** game_xaxis, int64_t * top_yvalue){
    
    //color, collumn,row
    int64_t x;
    int64_t max_start=current_size-1;
    if(max_start%2==0){
        x=max_start;
    }else{
        x=max_start-1;
    }

    
    while(x<=current_size){
        ///printf("start %"PRId64 " %"PRId64 " %"PRId64 " %"PRId64 "\n", x, max_start, x, current_size);
        short* collumn=game_xaxis[x];

        for(int64_t i=0; i<top_yvalue[x];i++){
            if(x%2==0 && x!=0){
                printf("%d -%" PRId64 " %" PRId64 "\n", collumn[i]-1,x/2,i);
            }else if(x==0){
                printf("%d %d %" PRId64 "\n", collumn[i]-1,0,i);
            }else{
                printf("%d %" PRId64 " %" PRId64 "\n", collumn[i]-1,(int64_t)x/2+1,i);
            }
        }
        x=counting_up(x);
    }

}

    
void vertical_candidates(int64_t  x, int64_t y, short ** game_xaxis, int64_t * top_yvalue, struct candidate **candidates, int64_t *cc){
    short* collumn=game_xaxis[x];
    short color=collumn[y];
    if(color<=0)return;
    int64_t count=1;
    int64_t uy=y;
    int64_t dy=y;
    
    //going down (south)
    for(int64_t i=y-1;i>-1;i=i-1){        
        if(collumn[i]!=color){
            break;
        }else{
            count++;
            //print64_tf("count %" PRId64 "\n",count);
            dy=i;
        }
    }
    
    //going up (north)
    for(int64_t i=y+1;i<top_yvalue[x];i++){
       if(collumn[i]!=color){
            break;
       
        }else{
            count++;
            uy=i;
        }
    }
    
    if(count>3){
        struct candidate *c=create_can(x, uy, x, dy);
        if(!check_in_candidates(candidates, c, *cc)){
            candidates[*cc]=c;
            *cc=*cc+1;
            //printf("vertical candidate ux:%" PRId64 ", uy:%" PRId64 ", dx:%" PRId64 " dy:%" PRId64 "\n", c->ux, c->uy,c->dx, c->dy);
        }
    }
}

void diagonal_horizontal_candidates(int64_t x, int64_t y,short ** game_xaxis, int64_t * top_yvalue,struct candidate **candidates, int64_t *cc, int64_t mode){
    
    short* collumn=game_xaxis[x];    
    short color=collumn[y];
    if(color<=0)return;

    int64_t count=1;
    int64_t dx =x;
    int64_t ux =x;
    int64_t dy =y;
    int64_t uy =y;
    
    //counting down (minus direction)
    int64_t i=x; //for value in table
    int64_t y_diag=y;
    while(true){
        i=counting_down(i);
        if(i>current_size-1)break;

        if(mode==1){
            y_diag-=1;
        }else if(mode==2){
            y_diag+=1;
        }
        
        short* nex_collumn=game_xaxis[i];
        if(top_yvalue[i]>0 && top_yvalue[i]> y_diag && y_diag>=0){
            short nex_color=nex_collumn[y_diag];
            if(nex_color!=color){
                break;
            }else{
                count++;
                dx=i;
                dy=y_diag;
            }  
        }else{
            break;
        }
    }
    
    //counting up (plus direction)
    i=x;
    y_diag=y;
    while(true){
        i=counting_up(i);
        if(mode==1){
            y_diag+=1;
        }else if(mode==2){
            y_diag-=1;
        }
        if(i>current_size-1)break;
        short* nex_collumn=game_xaxis[i];
        if(top_yvalue[i]>0 && top_yvalue[i]> y_diag && y_diag>=0){
            short nex_color=nex_collumn[y_diag];
            if(nex_color!=color){
                break;
            }else{
                count++;
                ux=i;
                uy=y_diag;
            }  
        }else{
            break;
        }
    }
    
    //printf("count %" PRId64 "\n",count);
    if(count>3){
        struct candidate *c=create_can(ux,uy, dx,dy);
        candidates[*cc]=c;
        *cc=*cc+1;
        //printf("diagonal/horizontal candidate ux:%" PRId64 ", uy:%" PRId64 ", dx:%" PRId64 " dy:%" PRId64 "\n", c->ux, c->uy,c->dx, c->dy);
        
    }
    
    
}

int removeCandidatesfromGame(short ** game_xaxis, int64_t * top_yvalue,struct candidate **candidates, int64_t cc, int64_t **affected_blocks, int64_t *count_affected ){

    int64_t *collumns_affected=calloc(current_size, sizeof(int64_t));
    if(collumns_affected==NULL){
        free(collumns_affected);
        return 0;
    }
    //mark blocks to be removed
    for(int64_t i=0; i<cc; i++){
        struct candidate *c=candidates[i];
        if(c->dx==c->ux){ //vertical line
            collumns_affected[c->dx]+=c->uy-c->dy+1;
            for(int64_t y=c->dy; y<=c->uy;y++){
                short* collumn=game_xaxis[c->dx];
                collumn[y]=0;
                num_blocks--;
            }
        }else{
            int64_t  x=c->dx;
            int64_t y=c->dy;
            while(x!=counting_up(c->ux)){ //go through the collumns
                collumns_affected[x]+=1;
                //Removing the block
                short* collumn=game_xaxis[x];
                collumn[y]=0;
                num_blocks--;
                x=counting_up(x);
                if(c->dy > c-> uy){ //downwards
                    y-=1;
                }else if (c->dy < c-> uy){//upwards
                    y+=1;
                }
            }
        }
    }
    
    //print_game_status(game_xaxis, top_yvalue);


    for(int64_t i=0;i<current_size; i++){
        if(collumns_affected[i]==0){
            continue;
        }
        //printf("affected %" PRId64 " \n",i);
        
        short *collumn=game_xaxis[i];
        int64_t j=0;
        while(j<top_yvalue[i]-1){
            //printf(" %" PRId64 " %" PRId64 " %" PRId64 " \n", i,j, collumn[j]); 
            if(collumn[j]==0){
                //printf("here\n");
                int64_t k=1;
                while((j+k)<top_yvalue[i] && collumn[j+k]==0 ){
                    k++;
                //printf("k %" PRId64 " ",k);
                }
                //printf(" %" PRId64 " \n", top_yvalue[i]-1);
                if(j+k>=top_yvalue[i]){
                    break;
                }
                
                //printf("moving %" PRId64 " %" PRId64 "  to %" PRId64 " %" PRId64 "\n", i, j+k,i,j);
                collumn[j]=collumn[j+k];
                collumn[j+k]=0;
                int64_t  *block=malloc(sizeof(int64_t)*2);
                block[0]=i;
                block[1]=j;
                if(!check_in_list(affected_blocks, *count_affected, i,j)){
                    affected_blocks[*count_affected]=block;
                    *count_affected=*count_affected+1;
                }
            }
            j++;
                
        }
        int64_t dif=collumns_affected[i];
        //printf("dif %" PRId64 " ", dif);
        //adapting top value of this collumn
        top_yvalue[i]=top_yvalue[i]-dif;

        
    }
    

    
    /*printf("affected Blocks\n");
    for(int i=0;i<*count_affected;i++){
        printf("x %" PRId64 ", y %" PRId64 " \n", affected_blocks[i][0],affected_blocks[i][1]);
    }*/

    free(collumns_affected);
    return 1;
   
    
}


/*compute candidates for this round, remove the corresponding lines and update game. 
 * Start a new round to be resolved with the affected blocks.
 */
int resolveRound(short ** game_xaxis, int64_t * top_yvalue,  int64_t  **relevant_blocks, int64_t num_relevant, int r){
    //if(r>1) printf("rec %d\n",r);
    struct candidate *candidates[num_blocks];
    int64_t cc=0; //count candidates
        

    for(int64_t i=0; i<num_relevant; i++){
        int64_t  x=relevant_blocks[i][0];
        int64_t y=(int64_t) relevant_blocks[i][1];
        //printf("checking %" PRId64 " %" PRId64 "\n", x,y);
        vertical_candidates(x, y,game_xaxis, top_yvalue, candidates, &cc);
        diagonal_horizontal_candidates(x, y,game_xaxis , top_yvalue,candidates, &cc, 0); //horizontal
        diagonal_horizontal_candidates(x, y,game_xaxis , top_yvalue,candidates, &cc, 1); //diagonal down
        diagonal_horizontal_candidates(x, y,game_xaxis ,top_yvalue , candidates, &cc, 2);//diagonal up
        

        
        
    }
    
    if(cc>0){
        //printf("show candidates:\n");
        //for(int i=0;i<cc;i++){
        //    struct candidate *c=candidates[i];
        //    printf("candidate ux:%" PRId64 ", uy:%" PRId64 ", dx:%" PRId64 " dy:%" PRId64 "\n", c->ux, c->uy,c->dx, c->dy);
        //}
        int64_t **affected_blocks=malloc(num_blocks*sizeof(int64_t)*2);
        if(affected_blocks==NULL){
            return 0;
        }
        
        int64_t count_affected=0;
        int succ= removeCandidatesfromGame(game_xaxis, top_yvalue,candidates, cc,affected_blocks, &count_affected );
        if(succ==0){
            for(int64_t i=0; i<count_affected;i++){
                free(affected_blocks[i]);
            }
            free(affected_blocks);
            return 0;
        }
        
        //print_game_status(game_xaxis, top_yvalue);
        if(count_affected>0){
           // printf("check affected bocks\n");
            int succ= resolveRound(game_xaxis, top_yvalue,  affected_blocks, count_affected, r+1);
            if(succ==0){
                for(int64_t i=0; i<count_affected;i++){
                    free(affected_blocks[i]);
                }
                free(affected_blocks);
                return 0;
            }
        }
        
        for(int64_t i=0; i<count_affected;i++){
            free(affected_blocks[i]);
        }
        free(affected_blocks);
    }

    for(int64_t i=0; i<cc;i++){
        free(candidates[i]);
    }
    return 1;
    
}

int grow_collumn(int64_t *collumn_size, short ** game_xaxis, int64_t x, int64_t *top_yvalue){
    int64_t size=collumn_size[x];
    int64_t new_size=size * 2;
    short * new_collumn = malloc((int64_t)sizeof(short) * new_size);
    if(new_collumn==NULL){
        free(new_collumn);
        return 0;
        
    }
    short *collumn=game_xaxis[x];
    for(int64_t i=0; i<top_yvalue[x]; i++){
        new_collumn[i]=collumn[i];
    }
    free(collumn);
    game_xaxis[x]=new_collumn;
    collumn_size[x]=new_size-1;
    return 1;
}



int main() {
    int maxchars=100;
    char *line = calloc(maxchars, sizeof(char) );
    bool reading=true;
    int returncode=0;
    
    current_size=100;
    short ** game_xaxis = (short **) calloc( current_size, sizeof(short*)); //TODO geht auch mit malloc
    int64_t * top_yvalue =(int64_t *) calloc(current_size, sizeof(int64_t)); 
    int64_t * collumn_size = (int64_t *)calloc(current_size, sizeof(int64_t)); 
    if(game_xaxis==NULL || top_yvalue==NULL || collumn_size==NULL){
        free(game_xaxis);
        free(top_yvalue);
        free(collumn_size);
        fprintf(stderr, "[ERROR]:Initial Calloc was not successful.\n");
        return 1;
    }

    
    num_blocks=0;

    while(reading){

        char *input = fgets(line, maxchars, stdin);
        /*
         * Die letzte Zeile kann, muss aber nicht mit einem Zeilenumbruch
         * terminiert werden 
        */
        if(input==NULL){ 
            reading=false;
            break;
        }
        //checking that the line only contains allowed characters
        int i=0;
        char ok_chars[13] = {' ', '-','\n', '0', '1', '2', '3', '4', '5','6', '7','8','9',};
        int whitespaces=0;
        
        int check_null=-1;
        while(i < maxchars && line[i]!='\n'){
            //printf(" %" PRId64 " %c\n", line[i], line[i]);
            if (line[i]==0 && check_null==-1){
                check_null=i;                
            }else if(line[i]!=0 && check_null!=-1){
                fprintf(stderr, "[ERROR]: Contains unaccepted NULL character.\n");
                returncode=1;
                break;
            }
            
            if(line[i]==ok_chars[0]) whitespaces++;
            
            bool ok=false;
            for(int j=0; j<13; j++){
                if(line[i]==ok_chars[j] || line[i]==0){
                    ok=true;
                }
            }
            
            if(!ok){
                fprintf(stderr, "[ERROR]: Contains unaccepted character '%c'.\n", line[i]);
                returncode=1;
                break;
            }
            i++;
        }

        if(whitespaces!=1){
            fprintf(stderr, "[ERROR]: Too many whitespaces: '%c'.\n", line[i]);
            returncode=1;
        }    
            
        //Tokening line and parsing the numbers into integers
        char *toke= strtok (line, " " );
        int count=0;
        //int *block=malloc(sizeof(int)*2);
        int64_t block[2];
        /*if(block==NULL){
                free(block);
                fprintf(stderr, "[ERROR]: Malloc was not successful.\n");
                returncode=1;
                break;
        }*/
        
        while (toke != NULL){
            char *end;
            const char *buff=toke;
            const int64_t sl = strtoll(buff, &end, 10);
            if (end == buff) {
                //free(block);
                fprintf(stderr, "[ERROR]:%s: not a decimal number\n", buff);
                returncode=1;
                break;

            /*} else if ('\0' != *end) {
                fprintf(stderr, "%s: extra characters at end of input: %s\n", buff, end);
            */
                
            /*} else if ((LONG_MIN == sl || LONG_MAX == sl) && ERANGE == errno) {
                fprintf(stderr, "[ERROR]:%s out of range of type long\n", buff);
                returncode=1;
                break;*/
            } else if (sl > 1048576) {
                fprintf(stderr, "[ERROR]:%" PRId64 " greater than 2^20 (1048576)\n", sl);
                returncode=1;
                break;
            } else if (sl < -1048576) {
                fprintf(stderr, "[ERROR]:%" PRId64 " less than -2^20\n (-1048576)", sl);
                returncode=1;
                break;
            } else {
                block[count]= sl;
                
            }
            
            count++;
            toke = strtok (NULL, " ");
            if(count==2 && toke !=NULL){
                fprintf(stderr, "[ERROR]:More than two values (also trailing whitespaces count) in Line.\n");
                returncode=1;
                break;
            }
        }
        if(count!=2){
            fprintf(stderr, "[ERROR]:Less than two values in Line.\n");
            returncode=1;
            break;
        }
        
       // printf(" %" PRId64 " %" PRId64 " ", block[0],block[1]);
        
        
        int64_t color=block[0];
        //sanity check
        if(color>254 || color<0){
            fprintf(stderr, "[ERROR]:Colors are only in [0,254], this block has %" PRId64 ".\n",color);
            returncode=1;
            break; 
        }
        //To ensure that Null is not mistaken for a value
        color=color+1;
        
        if(returncode==1){
            break;
        }
        
        
        num_blocks++;
        //Adapting the given x to our datastructer that also allows negative indices
        int64_t x=-1; //TODO: test if kleiner 2^30
        if(block[1]>0){
            x=block[1]*2-1;    
        }else{
            x=llabs(block[1])*2;
        }

        
        //printf("-----  x:%" PRId64 " (%" PRId64 ") y:%" PRId64 " color:%" PRId64 "  --------------\n", block[1],x,y,block[0]);
        
        if(x>=current_size){
            

            int64_t  new_size=x*(int64_t)2 % ((int64_t)1073741824*(int64_t)2);
            //printf("new size %" PRId64" %p \n",new_size, (void *) game_xaxis);
            game_xaxis = (short **)realloc(game_xaxis,  ((int64_t) sizeof(short *)) * new_size);
            top_yvalue = (int64_t *)realloc(top_yvalue,  ((int64_t) sizeof(int64_t *)) * new_size);
            collumn_size = (int64_t *)realloc(collumn_size,  ((int64_t) sizeof(int64_t *)) * new_size);

            if(game_xaxis== NULL || top_yvalue ==NULL || collumn_size==NULL){
                fprintf(stderr, "[ERROR]:Realloc after encountering large value was not successful" );
                returncode=1;
                break;  
            }
            
            //printf("realloc successful");
            for(int64_t i=current_size;i<new_size;i++){
                //printf("%" PRId64 " ", i);
                game_xaxis[i]=(short )0;
                top_yvalue[i]=(int64_t )0;
                collumn_size[i]=(int64_t )0;
            }
            
            current_size=new_size;

        }
        
        int64_t y=top_yvalue[x];
        
        if(collumn_size[x]==0){
            //printf("x %ld y %ld \n",x,y);

            //int * collumn =(int *) calloc(100, sizeof(int)); //TODO:eventuell auch mit malloc
            short * collumn =calloc(10, sizeof(short)); 
            if(collumn==NULL){
                free(collumn);
                fprintf(stderr, "[ERROR]: Malloc for collumn was not successful.\n");
                returncode=1;
                break;
            }
            game_xaxis[x]=collumn;
            collumn_size[x]=10-1; //weil wir bei 0 anfangen zu zählen
            //printf("creating new collumn x %" PRId64 " (=%" PRId64 ")\n",block[1] , x);
        }  
        //free(block);
    
        if(y>collumn_size[x]){
            int ok=grow_collumn(collumn_size,  game_xaxis,  x, top_yvalue);
            if(ok==0){
                returncode=1;
                fprintf(stderr, "[ERROR]: Malloc of larger collumn was not successful.\n");
                break;
            }

        }
        
        short* collumn=game_xaxis[x];
        collumn[y]=color;
        top_yvalue[x]+=1;
        
        //print_game_status(game_xaxis, top_yvalue);
        int64_t  **relevant_blocks=malloc(1*sizeof(int64_t )*2);
        int64_t  *relevant_block= malloc(sizeof(int64_t ) * 2);
        if(relevant_blocks==NULL || relevant_block==NULL){
            free(relevant_block);
            free(relevant_blocks);
            returncode=1;
            fprintf(stderr, "[ERROR]: Malloc of block was not successful.\n");
            break;
        }
        relevant_block[0]=x;
        relevant_block[1]=y;
        relevant_blocks[0]=relevant_block;
        int succ=resolveRound(game_xaxis,  top_yvalue, relevant_blocks, 1,1);
        free(relevant_block);
        free(relevant_blocks);
        if(succ==0){
            returncode=1;
            fprintf(stderr, "[ERROR]: Calloc during ResolveRounds was not successful.\n");
            break;
        }
        
        

    }
    
    if(returncode==0){
       // print_all_blocks(game_xaxis,top_yvalue);
    }
    

    if(game_xaxis!=NULL){
        for(int64_t i=0;i<current_size;i++){
        short *collumn=game_xaxis[i];
        if(collumn!=NULL){
            free(collumn);
        }
           
        }

        free(game_xaxis);

    }
    
    if(top_yvalue !=NULL ) free(top_yvalue);
    if(collumn_size !=NULL )free(collumn_size);
    if(line !=NULL )free(line);
    return returncode;
}
