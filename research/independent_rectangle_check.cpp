#include <algorithm>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <queue>
#include <vector>
struct P{int x,y;bool operator==(const P &b)const{return x==b.x&&y==b.y;}bool operator<(const P &b)const{return x<b.x||(x==b.x&&y<b.y);}};
bool on(P a,P b,P c){return (b.x-a.x)*(c.y-a.y)==(b.y-a.y)*(c.x-a.x);}
long hit(P p,const std::vector<P>&v){long t=0;for(size_t i=0;i<v.size();i++)for(size_t j=i+1;j<v.size();j++)t+=on(p,v[i],v[j]);return t;}
int main(){std::ifstream f("/private/tmp/no3-rectangle-input.txt");std::vector<P> p;int x,y;while(f>>x>>y)p.push_back({x,y});std::set<std::vector<P>> seen{p};std::queue<std::pair<std::vector<P>,int>> q;q.push({p,11});std::map<int,int> hist;long arcs=0;while(!q.empty()){auto [a,score]=q.front();q.pop();hist[score]++;for(int i=0;i<(int)a.size();i++)for(int j=i+1;j<(int)a.size();j++){P z=a[i],w=a[j],u{z.x,w.y},v{w.x,z.y};if(z.x==w.x||z.y==w.y||std::find(a.begin(),a.end(),u)!=a.end()||std::find(a.begin(),a.end(),v)!=a.end())continue;auto t=a;t.erase(t.begin()+j);t.erase(t.begin()+i);long d=-hit(z,t)-hit(w,t);for(P z1:t)d-=on(z,w,z1);d+=hit(u,t)+hit(v,t);for(P z1:t)d+=on(u,v,z1);if(score+d>12)continue;arcs++;t.push_back(u);t.push_back(v);std::sort(t.begin(),t.end());if(seen.insert(t).second)q.push({t,(int)(score+d)});}}std::cout<<"states "<<seen.size()<<" transitions "<<arcs<<"\n";for(auto [s,c]:hist)std::cout<<s<<" "<<c<<"\n";}
