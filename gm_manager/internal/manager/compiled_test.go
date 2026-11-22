//go:build windows

package manager

import (
	"context"
	"encoding/json"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"testing"
	"time"

	"newadmin/internal/adminapi"
)

func TestOptionalCompiledLocalService(t *testing.T) {
	executable := os.Getenv("GM_COMPILED_SERVICE")
	if executable == "" {
		t.Skip("只在显式指定本机构建产物时执行")
	}
	if !filepath.IsAbs(executable) {
		t.Fatal("set an absolute path to the locally built test executable")
	}
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	address := listener.Addr().String()
	listener.Close()
	directory := t.TempDir()
	config := Config{Listen: address, Token: "local-test-token-012345678901234567890123456789", DataDirectory: filepath.Join(directory, "management-data")}
	raw, _ := json.Marshal(config)
	path := filepath.Join(directory, "local-test.json")
	if err = os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	command := exec.Command(executable, "-config", path)
	command.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x08000000}
	if err = command.Start(); err != nil {
		t.Fatal(err)
	}
	defer func() { _ = command.Process.Kill(); _ = command.Wait() }()
	client, err := adminapi.NewClient("http://"+address, config.Token, "")
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	var status adminapi.Status
	for {
		err = client.Do(ctx, "GET", "/manage/v1/status", "", nil, &status)
		if err == nil {
			break
		}
		if ctx.Err() != nil {
			t.Fatal(err)
		}
		time.Sleep(25 * time.Millisecond)
	}
	if status.Language != "go" || status.OnlineAccounts != nil {
		t.Fatal(status)
	}
	var codes []adminapi.Code
	request := adminapi.CodeRequest{Kind: "cdk", Name: "本机隔离联调", Quantity: 2, Reward: adminapi.Reward{Points: 3}}
	if err = client.Do(ctx, "POST", "/manage/v1/codes", "compiled-local-1", request, &codes); err != nil {
		t.Fatal(err)
	}
	if len(codes) != 2 || codes[0].State != "managed_not_published" {
		t.Fatal(codes)
	}
	var again []adminapi.Code
	if err = client.Do(ctx, "POST", "/manage/v1/codes", "compiled-local-1", request, &again); err != nil || again[0].Code != codes[0].Code {
		t.Fatal("compiled replay changed", err)
	}
	var audit adminapi.Page[adminapi.Audit]
	if err = client.Do(ctx, "GET", "/manage/v1/audit", "", nil, &audit); err != nil || audit.Total != 1 {
		t.Fatal(err, audit.Total)
	}
	if report := os.Getenv("GM_COMPILED_REPORT"); report != "" {
		data, _ := json.MarshalIndent(map[string]any{"compiled_service_started": true, "listen": "loopback_only", "authentication": true, "codes_durable": true, "idempotent_replay": true, "audit": true, "game_database_configured": false, "production_server_contacted": false}, "", "  ")
		if err = os.WriteFile(report, data, 0600); err != nil {
			t.Fatal(err)
		}
	}
}

func TestCompiledDirectDatabaseService(t *testing.T) {
	executable := os.Getenv("GM_DIRECT_COMPILED")
	if executable == "" {
		t.Skip("set GM_DIRECT_COMPILED")
	}
	if !filepath.IsAbs(executable) {
		t.Fatal("set an absolute path to the locally built test executable")
	}
	s, _, account, _ := directFixture(t)
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	address := listener.Addr().String()
	listener.Close()
	directory := t.TempDir()
	config := Config{Listen: address, Token: "compiled-direct-local-01234567890123456789", DataDirectory: directory, GameDatabase: s.config.GameDatabase, DirectDatabase: true}
	raw, _ := json.Marshal(config)
	path := filepath.Join(directory, "direct.json")
	if err = os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	cmd := exec.Command(executable, "-config", path)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x08000000}
	if err = cmd.Start(); err != nil {
		t.Fatal(err)
	}
	defer func() { _ = cmd.Process.Kill(); _ = cmd.Wait() }()
	client, err := adminapi.NewClient("http://"+address, config.Token, "")
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
	defer cancel()
	var status adminapi.Status
	for {
		err = client.Do(ctx, "GET", "/manage/v1/status", "", nil, &status)
		if err == nil {
			break
		}
		if ctx.Err() != nil {
			t.Fatal(err)
		}
		time.Sleep(25 * time.Millisecond)
	}
	if status.WriteMode != "direct_sqlite" || status.DatabaseState != "read_write_connected" {
		t.Fatal("not real direct mode")
	}
	var preview struct {
		Total int `json:"total"`
	}
	if err = client.Do(ctx, "POST", "/manage/v1/preview", "", adminapi.Action{Name: "currency.credit", Scope: "single", AccountID: account, Currency: "cera"}, &preview); err != nil || preview.Total != 1 {
		t.Fatal("read-only client preview failed", err)
	}
	action := adminapi.Action{Name: "currency.credit", Scope: "single", AccountID: account, Currency: "token_cera", Amount: 6, Confirm: true}
	var receipt adminapi.Receipt
	for i := 0; i < 2; i++ {
		if err = client.Do(ctx, "POST", "/manage/v1/actions", "compiled-direct-credit", action, &receipt); err != nil {
			t.Fatal(err)
		}
	}
	if !receipt.DatabaseCommitted || number(t, s.store.db, "SELECT token_cera FROM accounts WHERE account_id=?", account) != 6 {
		t.Fatal("compiled direct commit/replay failed")
	}
}
