#include <algorithm>
#include <fstream>
#include <iostream>
#include <map>
#include <vector>
struct P { int x,y; bool operator==(const P &b)const{return x==b.x&&y==b.y;} };
bool on(P a,P b,P c){return (b.x-a.x)*(c.y-a.y)==(b.y-a.y)*(c.x-a.x);}
long conflicts(P p,const std::vector<P>&v){long t=0;for(size_t i=0;i<v.size();i++)for(size_t j=i+1;j<v.size();j++)t+=on(p,v[i],v[j]);return t;}
int main(){std::ifstream f("/private/tmp/no3-rectangle-input.txt");std::vector<P> p;int x,y;while(f>>x>>y)p.push_back({x,y});std::map<long,long> hist;long axis=0,occupied=0,legal=0;for(int i=0;i<(int)p.size();i++)for(int j=i+1;j<(int)p.size();j++){P a=p[i],b=p[j],u{a.x,b.y},v{b.x,a.y};if(a.x==b.x||a.y==b.y){axis++;continue;}if(std::find(p.begin(),p.end(),u)!=p.end()||std::find(p.begin(),p.end(),v)!=p.end()){occupied++;continue;}auto work=p;work.erase(work.begin()+j);work.erase(work.begin()+i);long delta=-conflicts(a,work)-conflicts(b,work);for(P q:work)delta-=on(a,b,q);delta+=conflicts(u,work)+conflicts(v,work);for(P q:work)delta+=on(u,v,q);hist[delta]++;legal++;}std::cout<<"axis "<<axis<<" occupied "<<occupied<<" legal "<<legal<<"\n";for(auto [d,c]:hist)std::cout<<d<<" "<<c<<"\n";}
