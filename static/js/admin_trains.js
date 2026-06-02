function setDefaultTime() {
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(9, 0, 0, 0);
    document.getElementById('departureTime').value = tomorrow.toISOString().slice(0, 16);
}

document.getElementById('addTrainForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const msgEl = document.getElementById('addTrainMsg');
    msgEl.className = 'message';
    msgEl.textContent = '';

    const data = {
        train_number: document.getElementById('trainNumber').value.trim(),
        departure: document.getElementById('departure').value.trim(),
        destination: document.getElementById('destination').value.trim(),
        departure_time: document.getElementById('departureTime').value,
        total_seats: parseInt(document.getElementById('totalSeats').value),
        price: parseFloat(document.getElementById('price').value)
    };

    if (!data.departure_time) {
        msgEl.className = 'message error';
        msgEl.textContent = '请选择出发时间';
        return;
    }

    try {
        const res = await fetch('/api/admin/add-train', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();

        if (result.success) {
            msgEl.className = 'message success';
            msgEl.textContent = '✅ 新列车添加成功！';
            document.getElementById('addTrainForm').reset();
            setDefaultTime();
        } else {
            msgEl.className = 'message error';
            msgEl.textContent = '❌ ' + result.msg;
        }
    } catch (err) {
        msgEl.className = 'message error';
        msgEl.textContent = '网络错误，请重试';
    }
});

async function updateTrain() {
    const oldTrainNumber = document.getElementById('old-train-number').value.trim();
    const newTrainNumber = document.getElementById('new-train-number').value.trim();
    const departureTime = document.getElementById('edit-departure-time').value;
    const price = document.getElementById('edit-price').value;

    if (!oldTrainNumber) {
        alert('请输入旧车次号');
        return;
    }
    if (!newTrainNumber) {
        alert('请输入新车次号');
        return;
    }
    if (!departureTime) {
        alert('请选择发车时间');
        return;
    }
    if (!price) {
        alert('请输入票价');
        return;
    }

    if (!confirm(`确认将车次 ${oldTrainNumber} 修改为 ${newTrainNumber}？`)) return;

    try {
        const res = await fetch('/api/admin/update-train', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                old_train_number: oldTrainNumber,
                new_train_number: newTrainNumber,
                departure_time: departureTime,
                price: parseFloat(price)
            })
        });

        const data = await res.json();
        if (data.success) {
            alert('✅ 修改成功');
        } else {
            alert('❌ ' + data.msg);
        }
    } catch (e) {
        alert('网络错误');
    }
}



document.addEventListener('DOMContentLoaded', setDefaultTime);