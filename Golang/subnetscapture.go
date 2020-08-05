package main

import (
	_ "bytes"
	"fmt"
	"github.com/Luxurioust/excelize"
	"golang.org/x/crypto/ssh"
	"golang.org/x/net/proxy"
	"io"
	"log"
	"net"
	"os"
	_ "regexp"
	"strconv"
	"strings"
	"sync"
	"time"
)

func main() {
	sheet := []string{"A","B","C","D"}
	//terface := make([]string, 5)
	//route := make([]string, 5)
	//var command string
	var filepath string
	//var iparry []string
	sshConfig := &ssh.ClientConfig{
		User: "username",
		Auth: []ssh.AuthMethod{
			ssh.Password("password"),
		},
		Timeout: 30 * time.Second,
		HostKeyCallback: func(hostname string, remote net.Addr, key ssh.PublicKey) error {
			return nil
		},

	}
	fmt.Println("Please input the excel path")
	fmt.Scanln(&filepath)
	iparry := readExcel(filepath)[:]
	for i, ip := range iparry {
		j:=0
		fmt.Println(i)
		fmt.Println(ip)
		IPaddress := ip + ":22"
		//fmt.Println(IPaddress)
		proxyauthen := &proxy.Auth{User: "socks5 jumper server username", Password: "password"}
		client, err := proxiedSSHClient("jumper server ip:socket port", IPaddress, proxyauthen, sshConfig)
		if err != nil {
			fmt.Println(err.Error())
			continue
		}

		session, err := client.NewSession()
		if err != nil {
			panic("Failed to create session: " + err.Error())
			//log.Println(err)
			continue
		}
		defer session.Close()

		modes := ssh.TerminalModes{
			ssh.ECHO:          1,     // disable echoing
			ssh.TTY_OP_ISPEED: 14400, // input speed = 14.4kbaud
			ssh.TTY_OP_OSPEED: 14400, // output speed = 14.4kbaud
		}

		if err := session.RequestPty("vt100", 80, 40, modes); err != nil {
			log.Fatal(err)
			//log.Println(err)
		}
		w, err := session.StdinPipe()
		if err != nil {
			panic(err)
			//log.Println(err)
		}
		r, err := session.StdoutPipe()
		if err != nil {
			panic(err)
			//log.Println(err)
		}
		e, err := session.StderrPipe()
		if err != nil {
			panic(err)
			//log.Println(err)
		}
		in, out := MuxShell(w, r, e)
		if err := session.Shell(); err != nil {
			log.Fatal(err)
			//log.Println(err)
		}
		<-out //ignore the shell output
		in <- "enable"
		in <- "enable password"
		in <- "terminal length 0"
		in <- "show ip int | in line protocol|Internet address"
		in <- "show run | in ip route"

		in <- "exit"
		in <- "exit"

		//fmt.Printf("%s\n%s\n%s\n%s\n%s\n", <-out, <-out, <-out, <-out, <-out)
		/*
			terface[i] = <-out
			fmt.Println("@@@@@@@@@@@@@@@@@")
			fmt.Println(terface[i])
			fmt.Println("@@@@@@@@@@@@@@@@@")
		*/
		i=i+1
		for xyz := range out {

			fmt.Println("@@@@@@@@@@@@@@@@@")
			fmt.Printf("%s\n", xyz)
			fmt.Println("+++++++++++++++++")
			fmt.Println(sheet[j] + strconv.Itoa(i))
			writexcel((sheet[j] + strconv.Itoa(i)),xyz,filepath)
			j=j+1
		}
		_, _, _, _, _ = <-out, <-out, <-out, <-out, <-out

		session.Wait()
	}

	time.Sleep(10 * time.Minute)
}

func proxiedSSHClient(proxyAddress, sshServerAddress string, P1 *proxy.Auth, sshConfig *ssh.ClientConfig) (*ssh.Client, error) {
	dialer, err := proxy.SOCKS5("tcp", proxyAddress, P1, proxy.Direct)
	if err != nil {
		return nil, err
		//log.Println(err)
	}

	conn, err := dialer.Dial("tcp", sshServerAddress)
	if err != nil {
		return nil, err
		//log.Println(err)
	}

	c, chans, reqs, err := ssh.NewClientConn(conn, sshServerAddress, sshConfig)
	if err != nil {
		return nil, err
		//log.Println(err)
	}

	return ssh.NewClient(c, chans, reqs), nil
}

func MuxShell(w io.Writer, r, e io.Reader) (chan<- string, <-chan string) {
	in := make(chan string, 3)
	out := make(chan string, 5)
	var wg sync.WaitGroup
	wg.Add(1) //for the shell itself
	go func() {
		for cmd := range in {
			//fmt.Println(cmd)
			//fmt.Println("+++++++++++++")
			wg.Add(1)
			w.Write([]byte(cmd + "\n"))
			//wg.Wait()
		}
	}()

	go func() {
		var (
			buf [65 * 1024]byte
			t   int
		)
		for {
			n, err := r.Read(buf[t:])
			if err != nil {
				//log.Println(err)
				fmt.Println(err.Error())
				close(in)
				close(out)
				return
			}
			t += n

			//fmt.Println(n)
			//fmt.Print("***********")
			//fmt.Println(t)

			result := string(buf[:t])
			if //strings.Contains(result, "Username:") ||
			//strings.Contains(result, "Password:") ||
			strings.Contains(result, "#") ||
				strings.Contains(result, ">") {
				out <- string(buf[:t])
				t = 0
				wg.Done()
			}
		}
	}()
	return in, out
}

func readExcel(excelPath string) []string {
	xlsx, err := excelize.OpenFile(excelPath)
	if err != nil {
		fmt.Println("open excel error,", err.Error())
		os.Exit(1)
	}
	rows, err := xlsx.GetRows(xlsx.GetSheetName(xlsx.GetActiveSheetIndex()))
	//fmt.Println(rows)
	result := make([]string, 0)
	for _, row := range rows {
		//fmt.Println(row[0])
		//fmt.Println(row[1])
		result = append(result, row[0])
		//result = append(result, row[1])
	}
	return result
}


func writexcel(axis string,value string,excelPath string){
	xlsx,_:= excelize.OpenFile(excelPath)
	index := xlsx.NewSheet("subnets")

	xlsx.SetCellValue("subnets", axis, value)
	// Set active sheet of the workbook.
	xlsx.SetActiveSheet(index)
	// Save xlsx file by the given path.
	err := xlsx.SaveAs(excelPath)
	if err != nil {
		fmt.Println(err)
	}
}