PCI Judger
============

PCI Judger = ProblemCI Judger

(叫FinalJudger是不是太嚣张了？)

以下所有命令均可添加--tmp指定临时目录

构建镜像
-----

```
docker build -t erjiaqing/finaljudge .
```

特性
-----
1. 支持SpecialJudge，事实上，所有题目都需要显式指明SpecialJudge，SpecialJudge的格式参考 MikeMirzayanov/testlib
2. 支持交互题，交互器的格式同样参考 MikeMirzayanov/testlib
3. 支持多组Case
4. 易于配置的语言

用法
-----

### 评测

```
./final_judger.py --problem {:problem} --code {:code} --language {:language} --action judge
```

评测结果会以JSON格式写入标准输出

**支持的语言**

```
C (GCC, C99)
C++ (G++, C++98), (G++, C++11)
CS (Mono)
Go (Go 1.9)
Haskell (GHC 1.7)
Java (Java 1.8)
Kotlin (Kotlin)
PHP (PHP 7.0)
Python (Python 3.6)
```

### 检查题目

```
./final_judger.py --problem {:problem} --action check
```

检查结果会以JSON格式输出

### 构建题目

```
./final_judger.py --problem {:problem} --dest {:problem_dest} --action build
```

将problem指定的目录的内容复制到problem_dest目录下，然后在problem_dest目录下构建

主要是构建checker

`problem` 不应与 `problem_dest` 相同
