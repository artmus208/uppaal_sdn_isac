import com.uppaal.engine.Engine;
import com.uppaal.engine.connection.LocalConnection;
import com.uppaal.model.core2.Document;
import com.uppaal.model.core2.DocumentPrototype;
import com.uppaal.model.io2.Problem;
import com.uppaal.model.system.*;
import com.uppaal.model.system.symbolic.*;
import java.io.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.TimeUnit;

/** Directed symbolic replay: only engine-derived successors may advance the path. */
public final class TimedReplay {
    static final int INF = Integer.MAX_VALUE;
    static final String MODEL_HASH = "5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385";
    static final String TRACE_HASH = "8186e1b68324ba288abe6249abdc73fa771400d95414d4bf77d2d1f9fdfbfcf7";
    static record Stored(int[] locations, int[] values, List<int[]> bounds) {}
    static record Trace(List<Stored> states, List<String> edges) {}
    static record Reach(SymbolicState state, List<SymbolicTransition> path) {}

    static String hash(Path p) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));
    }
    static Document loadModel(Path model) throws Exception {
        // DocumentPrototype 5.0 reads URI.getPath(), dropping a UNC authority.
        // Keep the host in the path itself: file:////host/share/file.xml.
        URI uri=model.toUri();
        if(uri.getAuthority()!=null) uri=URI.create("file://"+model.toString().replace('\\','/').replace(" ","%20"));
        return new DocumentPrototype().load(uri);
    }
    static void require(boolean ok, String message) {
        if (!ok) throw new IllegalArgumentException(message);
    }
    static final class Parser {
        final List<String> lines; int at;
        Parser(String text) {
            lines = new ArrayList<>();
            for (String line : text.split("\\R")) if (!line.isBlank()) lines.add(line.trim());
        }
        String next() { require(at < lines.size(), "Truncated XTR at line " + at); return lines.get(at++); }
        void dot() { require(next().equals("."), "Expected XTR separator at " + at); }
        int number() { return Integer.parseInt(next()); }
        int[] vector(int n) {
            int[] a = new int[n]; for (int i=0;i<n;i++) a[i]=number(); dot(); return a;
        }
        Stored state(int np, int nv, int nc) {
            int[] locations=vector(np); List<int[]> bounds=new ArrayList<>();
            while (!lines.get(at).equals(".")) {
                int i=number(), j=number(), bound=number(); dot();
                require(i>=0 && i<nc && j>=0 && j<nc, "Unknown XTR clock");
                bounds.add(new int[]{i,j,bound ^ 1}); // XTR flips the internal strictness bit.
            }
            dot(); return new Stored(locations, vector(nv), bounds);
        }
        Trace parse(int np, int nv, int nc) {
            List<Stored> states=new ArrayList<>(); List<String> edges=new ArrayList<>();
            states.add(state(np,nv,nc));
            while (at<lines.size() && !lines.get(at).equals(".")) {
                states.add(state(np,nv,nc)); StringBuilder e=new StringBuilder();
                while (!lines.get(at).equals(".")) e.append(next()).append(' ');
                dot(); edges.add(canonicalEdges(e.toString()));
            }
            dot(); require(at==lines.size(), "Trailing XTR content");
            require(edges.size()+1==states.size(), "State/transition count mismatch");
            return new Trace(states,edges);
        }
    }
    static String canonicalEdges(String s) {
        List<String> parts=new ArrayList<>();
        require(s.trim().endsWith(";"), "Missing XTR edge terminator");
        for (String part:s.split(";")) {
            if (part.isBlank()) continue;
            String[] words=part.trim().split("\\s+"); require(words.length>=2,"Incomplete XTR edge");
            List<String> numbers=new ArrayList<>();
            for (String word:words) numbers.add(Integer.toString(Integer.parseInt(word)));
            require(Integer.parseInt(words[0])>=0 && Integer.parseInt(words[1])>=0,"Negative edge ID");
            parts.add(String.join(" ",numbers));
        }
        require(!parts.isEmpty(),"Empty XTR transition");
        // Retain sender/receiver order, since update ordering matters.
        return String.join(" ; ",parts)+" ;";
    }
    static String edgeKey(SymbolicTransition transition) throws IOException {
        StringWriter w=new StringWriter();
        for (SystemEdgeSelect e:transition.getEdges()) e.writeXTRFormat(w);
        return canonicalEdges(w.toString());
    }
    static int[][] matrix(int n, List<int[]> constraints) {
        int[][] d=new int[n][n];
        for (int i=0;i<n;i++) { Arrays.fill(d[i],INF); d[i][i]=1; d[0][i]=1; }
        for (int[] c:constraints) d[c[0]][c[1]]=Math.min(d[c[0]][c[1]],c[2]);
        return close(d);
    }
    static int[][] close(int[][] d) {
        int n=d.length;
        for (int k=0;k<n;k++) for (int i=0;i<n;i++) {
            if (d[i][k]==INF) continue;
            for (int j=0;j<n;j++) {
                if (d[k][j]==INF) continue;
                long sum=(long)d[i][k]+d[k][j]-((d[i][k]|d[k][j])&1);
                if (sum<Integer.MIN_VALUE) throw new IllegalArgumentException("DBM lower bound overflow");
                d[i][j]=(int)Math.min(d[i][j],Math.min(INF,sum));
                if(i==j && d[i][j]<1) return null;
            }
        }
        for (int i=0;i<n;i++) if (d[i][i]<1) return null;
        return d;
    }
    static List<int[]> raw(Polyhedron p) {
        List<int[]> rows=new ArrayList<>();
        for (DBMConstraint c:p.getRawConstraintList()) rows.add(new int[]{c.i,c.j,c.bound});
        return rows;
    }
    static int[][] intersection(int[][] a,int[][] b) {
        if (a==null || b==null) return null;
        int[][] d=new int[a.length][a.length];
        for(int i=0;i<a.length;i++) for(int j=0;j<a.length;j++) d[i][j]=Math.min(a[i][j],b[i][j]);
        return close(d);
    }
    static SymbolicState restrict(UppaalSystem sys,SymbolicState reachable,int[][] d) {
        Polyhedron zone=new Polyhedron(sys);
        for(int i=0;i<d.length;i++) for(int j=0;j<d.length;j++)
            if(i!=j && d[i][j]!=INF) zone.add(i,j,d[i][j]);
        return new SymbolicState(reachable.getLocationVector().clone(),reachable.getVariableValues().clone(),zone);
    }
    static boolean discreteMatch(SymbolicState actual, Stored saved) {
        if (!Arrays.equals(actual.getVariableValues(),saved.values())) return false;
        SystemLocation[] loc=actual.getLocationVector();
        if (loc.length!=saved.locations().length) return false;
        for(int i=0;i<loc.length;i++) if(loc[i].getIndex()!=saved.locations()[i]) return false;
        return true;
    }
    static String json(Object value) {
        if(value==null) return "null";
        if(value instanceof Number || value instanceof Boolean) return value.toString();
        if(value instanceof Map<?,?> m) {
            List<String> a=new ArrayList<>(); for(var e:m.entrySet()) a.add(json(e.getKey().toString())+":"+json(e.getValue()));
            return "{"+String.join(",",a)+"}";
        }
        if(value instanceof Iterable<?> it) { List<String>a=new ArrayList<>();for(Object x:it)a.add(json(x));return "["+String.join(",",a)+"]"; }
        if(value instanceof int[] a) { List<Integer> b=new ArrayList<>();for(int x:a)b.add(x);return json(b); }
        if(value instanceof int[][] a) return json(Arrays.asList(a));
        return "\""+value.toString().replace("\\","\\\\").replace("\"","\\\"").replace("\n","\\n").replace("\r","\\r").replace("\t","\\t")+"\"";
    }
    static void event(PrintWriter out,Map<String,Object> e) { out.println(json(e));out.flush(); }
    static void savePath(Path p,List<SymbolicTransition> path) throws Exception {
        try(Writer w=Files.newBufferedWriter(p,StandardCharsets.UTF_8)) {
            path.get(0).getTarget().writeXTRFormat(w);
            for(int i=1;i<path.size();i++) path.get(i).writeXTRFormat(w);
            w.write(".\n");
        }
    }
    static int index(UppaalSystem sys,String name,boolean clock) {
        int count=clock?sys.getNoOfClocks():sys.getNoOfVariables();
        for(int i=0;i<count;i++) if(name.equals(clock?sys.getClockName(i):sys.getVariableName(i))) return i;
        throw new IllegalArgumentException("Missing compiled binding: "+name);
    }
    static Map<String,Object> selected(UppaalSystem sys,SymbolicState s) {
        Map<String,Object> m=new LinkedHashMap<>();
        for(String name:List.of("family_grant_0","u0_mac_queue_q","u0_mac_queue_overflow_seen","u0_mac_scheduleMode","u0_app_service_request_pending"))
            m.put(name,s.getVariableValues()[index(sys,name,false)]);
        return m;
    }
    static void selftest(Path trace) throws Exception {
        require(matrix(2,List.of(new int[]{0,1,-1},new int[]{1,0,1}))==null,"Empty zone accepted");
        require(matrix(2,List.of(new int[]{0,1,1},new int[]{1,0,0}))==null,"Strict equality conflict accepted");
        require(matrix(2,List.of(new int[]{0,1,-1},new int[]{1,0,3}))!=null,"Clock=1 rejected");
        int[][] a=matrix(2,List.of(new int[]{0,1,1},new int[]{1,0,1}));
        int[][] b=matrix(2,List.of(new int[]{0,1,-1},new int[]{1,0,3}));
        require(intersection(a,b)==null,"Disjoint zones accepted");
        Trace parsed=new Parser(Files.readString(trace)).parse(50,255,70);
        require(parsed.states().size()==69,"Unexpected original trace length");
        require(parsed.edges().size()==68,"Unexpected edge count");
        require(parsed.edges().get(67).equals("21 1 0 ;"),"Lost select value");
        try { new Parser(Files.readString(trace)+"junk").parse(50,255,70); throw new AssertionError("Trailing junk accepted"); }
        catch(IllegalArgumentException expected) {}
        require(canonicalEdges("1 2 -1 ; 3 4 ;").equals("1 2 -1 ; 3 4 ;"),"Select/sync parser changed order");
        System.out.println("Parser and DBM controls OK; 69 states / 68 transitions; no engine invoked");
    }
    static int replay(String[] args) throws Exception {
        Path model=Path.of(args[1]),traceFile=Path.of(args[2]),out=Path.of(args[3]);String mode=args[4];
        require(hash(model).equals(MODEL_HASH),"Baseline model hash mismatch");
        require(hash(traceFile).equals(TRACE_HASH),"Manual trace hash mismatch");
        require(List.of("replay","negative-discrete","negative-clock").contains(mode),"Unknown replay mode");
        Files.createDirectories(out);
        Engine engine=new Engine();LocalConnection connection=new LocalConnection("replay-local",new File(args[0]));
        engine.resetConnections(List.of(connection));
        long start=System.nanoTime(); int result=2;
        Map<String,Object> report=new LinkedHashMap<>();
        report.put("evidence_kind","engine_directed_symbolic_replay");report.put("property_verdict",null);
        report.put("model_hash",MODEL_HASH);report.put("trace_hash",TRACE_HASH);report.put("mode",mode);
        try(PrintWriter events=new PrintWriter(Files.newBufferedWriter(out.resolve("steps.jsonl"),StandardCharsets.UTF_8))) {
            engine.connect().get(10,TimeUnit.SECONDS);
            report.put("actual_engine_version",engine.getVersion().get(10,TimeUnit.SECONDS));
            ArrayList<Problem> problems=new ArrayList<>();
            Document doc=loadModel(model);
            UppaalSystem sys=engine.getSystem(doc,problems).get(20,TimeUnit.SECONDS);
            for(Problem p:problems) require("warning".equals(p.getType()),"Compilation: "+p);
            report.put("processes",sys.getNoOfProcesses());report.put("variables",sys.getNoOfVariables());report.put("clocks",sys.getNoOfClocks());
            report.put("clock_names",sys.getClockNames());report.put("variable_names",sys.getVariables());
            Trace trace=new Parser(Files.readString(traceFile)).parse(sys.getNoOfProcesses(),sys.getNoOfVariables(),sys.getNoOfClocks());
            List<Stored> saved=new ArrayList<>(trace.states());int last=saved.size()-1;
            if(mode.equals("negative-discrete")) {
                Stored s=saved.get(last);int[] values=s.values().clone();values[index(sys,"family_grant_0",false)]=0;
                saved.set(last,new Stored(s.locations(),values,s.bounds()));
            }
            if(mode.equals("negative-clock")) {
                Stored s=saved.get(last);int clock=index(sys,"shared_load.tick",true);
                // Well-formed nonempty zone shared_load.tick=1. Final edge resets this clock to zero.
                saved.set(last,new Stored(s.locations(),s.values(),List.of(new int[]{0,clock,-1},new int[]{clock,0,3})));
            }
            SymbolicState initial=engine.getInitialState(sys).get(10,TimeUnit.SECONDS);
            require(discreteMatch(initial,saved.get(0)),"Engine initial integers/locations differ");
            int nc=sys.getNoOfClocks();int[][] zone=intersection(matrix(nc,raw(initial.getPolyhedron())),matrix(nc,saved.get(0).bounds()));
            require(zone!=null,"Engine initial zone does not intersect saved initial zone");
            SymbolicState first=restrict(sys,initial,zone);
            List<Reach> frontier=List.of(new Reach(first,List.of(new SymbolicTransition(null,null,first))));
            int accepted=0;
            event(events,new LinkedHashMap<>(Map.of("state_index",0,"reachable_zone",zone,"selected",selected(sys,first))));
            for(int step=1;step<saved.size();step++) {
                require((System.nanoTime()-start)/1e9<55,"Internal replay wall budget exceeded");
                Stored target=saved.get(step);int[][] targetZone=matrix(nc,target.bounds());
                require(targetZone!=null,"Malformed/empty stored zone at "+step);
                Map<String,Reach> next=new LinkedHashMap<>();int enabled=0,edgeMatches=0,discreteMatches=0;
                for(Reach reach:frontier) {
                    List<SymbolicTransition> choices=engine.getTransitions(sys,reach.state()).get(20,TimeUnit.SECONDS);
                    enabled+=choices.size();
                    for(SymbolicTransition choice:choices) {
                        if(choice.getTarget()==null || !choice.hasEdges()) continue;
                        if(!edgeKey(choice).equals(trace.edges().get(step-1))) continue;
                        edgeMatches++;
                        if(!discreteMatch(choice.getTarget(),target)) continue;
                        discreteMatches++;
                        int[][] common=intersection(matrix(nc,raw(choice.getTarget().getPolyhedron())),targetZone);
                        if(common==null) continue;
                        SymbolicState restricted=restrict(sys,choice.getTarget(),common);
                        List<SymbolicTransition> path=new ArrayList<>(reach.path());
                        path.add(new SymbolicTransition(reach.state(),choice.getEdges(),restricted));
                        next.putIfAbsent(Arrays.deepToString(common),new Reach(restricted,path));
                    }
                }
                Map<String,Object> log=new LinkedHashMap<>();log.put("state_index",step);log.put("stored_edges",trace.edges().get(step-1));
                log.put("enabled_successors",enabled);log.put("edge_matches",edgeMatches);log.put("discrete_matches",discreteMatches);log.put("reachable_frontier",next.size());
                if(next.isEmpty()) {
                    String reason=edgeMatches==0?"edge_select_not_enabled":discreteMatches==0?"discrete_state_mismatch":"clock_zone_disjoint";
                    log.put("rejection",reason);event(events,log);
                    report.put("status","rejected");report.put("first_unavailable_state_index",step);report.put("reason",reason);
                    savePath(out.resolve("reachable-prefix.xtr"),frontier.get(0).path());result=1;break;
                }
                require(next.size()<=8,"Ambiguous frontier exceeds fixed limit; inconclusive");
                frontier=new ArrayList<>(next.values());accepted=step;
                log.put("reachable_zone",matrix(nc,raw(frontier.get(0).state().getPolyhedron())));
                log.put("selected",selected(sys,frontier.get(0).state()));event(events,log);
                System.out.println("Accepted state "+step+" / "+last+"; enabled="+enabled+"; frontier="+next.size());
                if(step==last) {
                    report.put("status","replay_complete");report.put("selected_final_values",selected(sys,frontier.get(0).state()));
                    report.put("final_time_zone",matrix(nc,raw(frontier.get(0).state().getPolyhedron()))[1][0]);
                    savePath(out.resolve("reachable-prefix.xtr"),frontier.get(0).path());result=0;
                }
            }
            report.put("accepted_transitions",accepted);report.put("stored_states",saved.size());
            report.put("semantics","Nonempty reachable intersection at each saved state; no imported discrete state is used as an initial state");
            if(!mode.equals("replay")) report.put("control_expected_rejection",result==1 && accepted==last-1 && report.get("reason").equals(mode.equals("negative-clock")?"clock_zone_disjoint":"discrete_state_mismatch"));
        } catch(Exception e) {
            report.put("status","error");report.put("error",e.toString());e.printStackTrace(System.err);result=2;
        } finally {
            connection.kill();
            report.put("elapsed_seconds",(System.nanoTime()-start)/1e9);
            Files.writeString(out.resolve("result.json"),json(report)+"\n",StandardCharsets.UTF_8);
        }
        System.out.println(json(report));return result;
    }
    public static void main(String[] args) {
        int result=2;
        try {
            if(args.length==2 && args[0].equals("--self-test")) { selftest(Path.of(args[1]));result=0; }
            else if(args.length==2 && args[0].equals("--model-test")) { require(loadModel(Path.of(args[1])).getTemplateList().size()==50,"Model did not load");System.out.println("Baseline XML loaded: 50 templates; engine not invoked");result=0; }
            else { require(args.length==5,"Usage: TimedReplay SERVER MODEL TRACE OUTPUT MODE"); result=replay(args); }
        } catch(Exception e) { e.printStackTrace(System.err); }
        System.exit(result); // Engine owns an executor; connection is killed in replay's finally.
    }
}
